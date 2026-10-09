// Package agent is the incident-triage agent loop for the Kestrel platform team.
// It drives the Claude Messages API through anthropic-sdk-go, executes read-only
// platform tools on the model's behalf and returns the final answer.
// See README.md for the requirements.
package agent

import (
	"cmp"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/anthropics/anthropic-sdk-go"
	"golang.org/x/sync/errgroup"
)

// ToolFunc runs one tool call. input is the raw JSON object the model produced.
// The returned string is sent back to the model as the tool_result content.
type ToolFunc func(ctx context.Context, input json.RawMessage) (string, error)

// Tool is one entry in the registry.
type Tool struct {
	Name        string
	Description string
	// Properties is the JSON-schema "properties" object for the input.
	Properties map[string]any
	// Required lists the property names that must be present.
	Required []string
	Handler  ToolFunc
}

// Config tunes the loop. Zero values get defaults (see README).
type Config struct {
	Model       anthropic.Model // default anthropic.ModelClaudeSonnet5_5
	System      string
	MaxTokens   int64         // default 2048
	MaxTurns    int           // default 8; one turn = one Messages API call
	MaxParallel int           // default 4; concurrent tool calls within a turn
	ToolTimeout time.Duration // default 20s; per tool call
}

// Usage is the token usage summed over every Messages API call in a run.
type Usage struct {
	InputTokens  int64
	OutputTokens int64
}

// Result is what a run produced.
type Result struct {
	Text       string                   // text blocks of the final assistant message, joined with "\n"
	StopReason anthropic.StopReason     // stop reason of the final call
	Turns      int                      // Messages API calls made
	ToolCalls  int                      // tool_use blocks executed (including ones that became is_error)
	Usage      Usage                    // summed over all calls
	Messages   []anthropic.MessageParam // full transcript, including the initial user prompt
}

// MaxTurnsError is returned when the model still wants tools after MaxTurns calls.
type MaxTurnsError struct{ Turns int }

func (e *MaxTurnsError) Error() string {
	return fmt.Sprintf("agent: turn budget exhausted after %d turns", e.Turns)
}

var (
	// ErrMaxTokens: the final response was cut off by max_tokens.
	ErrMaxTokens = errors.New("agent: response truncated at max_tokens")
	// ErrRefusal: the model refused (stop_reason "refusal").
	ErrRefusal = errors.New("agent: model refused the request")
)

// Agent is safe for concurrent Run calls once constructed.
type Agent struct {
	client anthropic.Client
	cfg    Config
	tools  map[string]Tool
	params []anthropic.ToolUnionParam
}

// New validates the tools and builds an Agent.
func New(client anthropic.Client, cfg Config, tools ...Tool) (*Agent, error) {
	cfg.Model = cmp.Or(cfg.Model, anthropic.ModelClaudeSonnet5_5)
	cfg.MaxTokens = cmp.Or(cfg.MaxTokens, 2048)
	cfg.MaxTurns = cmp.Or(cfg.MaxTurns, 8)
	cfg.MaxParallel = cmp.Or(cfg.MaxParallel, 4)
	cfg.ToolTimeout = cmp.Or(cfg.ToolTimeout, 20*time.Second)
	if cfg.MaxTurns < 1 || cfg.MaxParallel < 1 {
		return nil, errors.New("agent: MaxTurns and MaxParallel must be positive")
	}

	a := &Agent{client: client, cfg: cfg, tools: make(map[string]Tool, len(tools))}
	for _, t := range tools {
		switch {
		case t.Name == "":
			return nil, errors.New("agent: tool with empty name")
		case t.Handler == nil:
			return nil, fmt.Errorf("agent: tool %q has no handler", t.Name)
		}
		if _, dup := a.tools[t.Name]; dup {
			return nil, fmt.Errorf("agent: duplicate tool %q", t.Name)
		}
		a.tools[t.Name] = t
		tp := anthropic.ToolParam{
			Name:        t.Name,
			Description: anthropic.String(t.Description),
			InputSchema: anthropic.ToolInputSchemaParam{Properties: t.Properties, Required: t.Required},
		}
		a.params = append(a.params, anthropic.ToolUnionParam{OfTool: &tp})
	}
	return a, nil
}

// Run executes the agent loop for one user prompt.
func (a *Agent) Run(ctx context.Context, prompt string) (Result, error) {
	res := Result{Messages: []anthropic.MessageParam{
		anthropic.NewUserMessage(anthropic.NewTextBlock(prompt)),
	}}

	for {
		if res.Turns >= a.cfg.MaxTurns {
			return res, &MaxTurnsError{Turns: res.Turns}
		}
		params := anthropic.MessageNewParams{
			Model:     a.cfg.Model,
			MaxTokens: a.cfg.MaxTokens,
			Messages:  res.Messages,
			Tools:     a.params,
		}
		if a.cfg.System != "" {
			params.System = []anthropic.TextBlockParam{{Text: a.cfg.System}}
		}
		msg, err := a.client.Messages.New(ctx, params)
		if err != nil {
			return res, fmt.Errorf("agent: turn %d: %w", res.Turns+1, err)
		}
		res.Turns++
		res.Usage.InputTokens += msg.Usage.InputTokens
		res.Usage.OutputTokens += msg.Usage.OutputTokens
		res.StopReason = msg.StopReason
		res.Messages = append(res.Messages, msg.ToParam())

		switch msg.StopReason {
		case anthropic.StopReasonEndTurn, anthropic.StopReasonStopSequence:
			res.Text = text(msg)
			return res, nil
		case anthropic.StopReasonMaxTokens:
			res.Text = text(msg)
			return res, ErrMaxTokens
		case anthropic.StopReasonRefusal:
			res.Text = text(msg)
			return res, ErrRefusal
		case anthropic.StopReasonToolUse:
			// handled below
		default:
			return res, fmt.Errorf("agent: unexpected stop_reason %q", msg.StopReason)
		}

		var calls []anthropic.ToolUseBlock
		for _, b := range msg.Content {
			if b.Type == "tool_use" {
				calls = append(calls, b.AsToolUse())
			}
		}
		if len(calls) == 0 {
			return res, errors.New("agent: stop_reason tool_use without tool_use blocks")
		}
		results, err := a.runTools(ctx, calls)
		if err != nil {
			return res, err
		}
		res.ToolCalls += len(calls)
		res.Messages = append(res.Messages, anthropic.NewUserMessage(results...))
	}
}

// runTools executes every call of one turn concurrently (bounded) and returns
// the tool_result blocks in the same order as the tool_use blocks.
func (a *Agent) runTools(ctx context.Context, calls []anthropic.ToolUseBlock) ([]anthropic.ContentBlockParamUnion, error) {
	out := make([]anthropic.ContentBlockParamUnion, len(calls))
	g, gctx := errgroup.WithContext(ctx)
	g.SetLimit(a.cfg.MaxParallel)
	for i, c := range calls {
		g.Go(func() error {
			content, isErr := a.call(gctx, c)
			out[i] = anthropic.NewToolResultBlock(c.ID, content, isErr)
			return nil // tool failures are data for the model, not loop errors
		})
	}
	_ = g.Wait()
	if err := ctx.Err(); err != nil {
		return nil, fmt.Errorf("agent: cancelled during tool execution: %w", err)
	}
	return out, nil
}

// call runs one tool and maps every failure to an is_error result the model can act on.
func (a *Agent) call(ctx context.Context, c anthropic.ToolUseBlock) (content string, isErr bool) {
	t, ok := a.tools[c.Name]
	if !ok {
		return fmt.Sprintf("unknown tool %q; available tools: %s", c.Name, a.names()), true
	}
	if err := validate(c.Input, t.Required); err != nil {
		return "invalid input: " + err.Error(), true
	}
	ctx, cancel := context.WithTimeout(ctx, a.cfg.ToolTimeout)
	defer cancel()
	defer func() {
		if r := recover(); r != nil {
			content, isErr = fmt.Sprintf("tool %q failed: internal error", c.Name), true
		}
	}()
	s, err := t.Handler(ctx, c.Input)
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) && ctx.Err() != nil {
			return fmt.Sprintf("tool %q timed out after %s", c.Name, a.cfg.ToolTimeout), true
		}
		return fmt.Sprintf("tool %q failed: %v", c.Name, err), true
	}
	return s, false
}

func validate(raw json.RawMessage, required []string) error {
	var obj map[string]json.RawMessage
	if err := json.Unmarshal(raw, &obj); err != nil || obj == nil {
		return errors.New("input must be a JSON object")
	}
	var missing []string
	for _, k := range required {
		if v, ok := obj[k]; !ok || string(v) == "null" {
			missing = append(missing, k)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("missing required field(s): %s", strings.Join(missing, ", "))
	}
	return nil
}

func (a *Agent) names() string {
	var n []string
	for _, p := range a.params {
		n = append(n, p.OfTool.Name)
	}
	return strings.Join(n, ", ")
}

func text(msg *anthropic.Message) string {
	var parts []string
	for _, b := range msg.Content {
		if b.Type == "text" {
			parts = append(parts, b.AsText().Text)
		}
	}
	return strings.Join(parts, "\n")
}

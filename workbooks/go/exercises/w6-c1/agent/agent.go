// Package agent is the incident-triage agent loop for the Kestrel platform team.
// It drives the Claude Messages API through anthropic-sdk-go, executes read-only
// platform tools on the model's behalf and returns the final answer.
// See README.md for the requirements.
package agent

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/anthropics/anthropic-sdk-go"
	_ "golang.org/x/sync/errgroup" // you will want errgroup for parallel tool calls
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
	// TODO: tool registry and the []anthropic.ToolUnionParam sent on every request.
}

var errNotImplemented = errors.New("agent: not implemented")

// New validates the tools and builds an Agent.
//
// TODO:
//   - apply Config defaults (README "Defaults")
//   - reject empty names, nil handlers and duplicate names
//   - build one anthropic.ToolParam per tool (name, description, input_schema)
func New(client anthropic.Client, cfg Config, tools ...Tool) (*Agent, error) {
	_ = tools
	return nil, errNotImplemented
}

// Run executes the agent loop for one user prompt.
//
// TODO (README "Requirements"):
//   - call a.client.Messages.New with the transcript and the tools every turn
//   - append the assistant message (msg.ToParam()) to the transcript
//   - switch on msg.StopReason
//   - for tool_use: run every tool_use block of the turn concurrently, then send
//     ONE user message with one tool_result per tool_use, same order, same ids
//   - unknown tool / invalid input / handler error / panic / timeout -> is_error result
//   - enforce MaxTurns, honour ctx, sum usage
func (a *Agent) Run(ctx context.Context, prompt string) (Result, error) {
	_ = ctx
	_ = prompt
	_ = json.RawMessage(nil)
	_ = time.Second
	_ = fmt.Sprintf
	return Result{}, errNotImplemented
}

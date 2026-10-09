package agent

import (
	"context"
	"encoding/json"
	"errors"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/anthropics/anthropic-sdk-go"
)

func mustNew(t *testing.T, f *fakeAPI, cfg Config, tools ...Tool) *Agent {
	t.Helper()
	a, err := New(f.client(), cfg, tools...)
	if err != nil {
		t.Fatalf("New: %v", err)
	}
	return a
}

func lastUser(t *testing.T, r apiRequest) []contentBlock {
	t.Helper()
	if len(r.Messages) == 0 {
		t.Fatal("request has no messages")
	}
	m := r.Messages[len(r.Messages)-1]
	if m.Role != "user" {
		t.Fatalf("last message role = %q, want user", m.Role)
	}
	return m.Content
}

func TestHiddenNewRejectsBadRegistry(t *testing.T) {
	f := newFake(t)
	noHandler := metricsTool()
	noHandler.Handler = nil
	cases := map[string][]Tool{
		"duplicate": {metricsTool(), metricsTool()},
		"empty":     {{Name: "", Handler: metricsTool().Handler}},
		"nil":       {noHandler},
	}
	for name, tools := range cases {
		if _, err := New(f.client(), testConfig(), tools...); err == nil {
			t.Errorf("%s: New should fail", name)
		}
	}
}

func TestHiddenRequestShapeToolsSystemModel(t *testing.T) {
	f := newFake(t, finalTurn(10, 5, "nothing to do"))
	cfg := testConfig()
	a := mustNew(t, f, cfg, podEventsTool(nil), metricsTool())
	if _, err := a.Run(context.Background(), "hi"); err != nil {
		t.Fatal(err)
	}
	r := f.requests()[0]
	if len(r.Tools) != 2 || r.Tools[0].Name != "get_pod_events" || r.Tools[1].Name != "query_metrics" {
		t.Fatalf("tools sent = %+v, want both tools in registration order", r.Tools)
	}
	if r.Tools[0].Description == "" {
		t.Fatal("tool description not sent: descriptions are how the model picks tools")
	}
	sch := r.Tools[0].InputSchema
	if sch["type"] != "object" || sch["properties"] == nil {
		t.Fatalf("input_schema = %v, want type object with properties", sch)
	}
	req, _ := sch["required"].([]any)
	if len(req) != 2 {
		t.Fatalf("input_schema.required = %v", sch["required"])
	}
	if len(r.System) == 0 || !strings.Contains(r.System[0].Text, "triage") {
		t.Fatalf("system prompt not sent: %+v", r.System)
	}
	if r.MaxTokens != 1024 || r.Model == "" {
		t.Fatalf("model=%q max_tokens=%d", r.Model, r.MaxTokens)
	}
	if len(r.Messages) != 1 || r.Messages[0].Role != "user" || r.Messages[0].Content[0].Text != "hi" {
		t.Fatalf("first request messages = %+v", r.Messages)
	}
}

func TestHiddenDefaultsApplied(t *testing.T) {
	f := newFake(t, finalTurn(1, 1, "ok"))
	a := mustNew(t, f, Config{}, metricsTool())
	if _, err := a.Run(context.Background(), "x"); err != nil {
		t.Fatal(err)
	}
	r := f.requests()[0]
	if r.MaxTokens != 2048 || r.Model != string(anthropic.ModelClaudeSonnet5_5) {
		t.Fatalf("defaults: model=%q max_tokens=%d, want %q/2048", r.Model, r.MaxTokens, anthropic.ModelClaudeSonnet5_5)
	}
	if len(r.System) != 0 {
		t.Fatal("empty System must not send a system block")
	}
}

func TestHiddenParallelToolCallsRunConcurrentlyOneUserMessage(t *testing.T) {
	f := newFake(t,
		toolTurn(100, 30, "",
			toolUse{"toolu_a", "slow_a", `{}`},
			toolUse{"toolu_b", "slow_b", `{}`},
			toolUse{"toolu_c", "query_metrics", `{"promql":"up"}`},
		),
		finalTurn(200, 20, "done"),
	)
	// slow_a and slow_b each wait until the other has started: sequential
	// execution deadlocks and the barrier times out.
	var started sync.WaitGroup
	started.Add(2)
	barrier := func(name, out string) Tool {
		return Tool{Name: name, Description: "barrier", Handler: func(ctx context.Context, _ json.RawMessage) (string, error) {
			started.Done()
			done := make(chan struct{})
			go func() { started.Wait(); close(done) }()
			select {
			case <-done:
				if name == "slow_a" {
					time.Sleep(50 * time.Millisecond) // finish last to test ordering
				}
				return out, nil
			case <-time.After(1500 * time.Millisecond):
				return "", errors.New("barrier timeout: tools ran sequentially")
			}
		}}
	}
	a := mustNew(t, f, testConfig(), barrier("slow_a", "A"), barrier("slow_b", "B"), metricsTool())
	res, err := a.Run(context.Background(), "go")
	if err != nil {
		t.Fatal(err)
	}
	if res.ToolCalls != 3 {
		t.Fatalf("ToolCalls = %d, want 3", res.ToolCalls)
	}
	reqs := f.requests()
	if len(reqs) != 2 {
		t.Fatalf("API calls = %d, want 2 (all tool results go back in ONE request)", len(reqs))
	}
	blocks := lastUser(t, reqs[1])
	if len(blocks) != 3 {
		t.Fatalf("user message has %d blocks, want 3 tool_result blocks in one message", len(blocks))
	}
	wantIDs := []string{"toolu_a", "toolu_b", "toolu_c"}
	wantText := []string{"A", "B", ""}
	for i, b := range blocks {
		if b.Type != "tool_result" || b.ToolUseID != wantIDs[i] {
			t.Fatalf("block %d = %s/%s, want tool_result for %s (same order as tool_use blocks)", i, b.Type, b.ToolUseID, wantIDs[i])
		}
		if b.IsError {
			t.Fatalf("block %d is_error: %s", i, b.resultText())
		}
		if wantText[i] != "" && b.resultText() != wantText[i] {
			t.Fatalf("block %d content = %q, want %q", i, b.resultText(), wantText[i])
		}
	}
	// The assistant turn with the tool_use blocks must precede the results.
	prev := reqs[1].Messages[len(reqs[1].Messages)-2]
	if prev.Role != "assistant" {
		t.Fatalf("message before tool results has role %q, want assistant", prev.Role)
	}
	n := 0
	for _, b := range prev.Content {
		if b.Type == "tool_use" {
			n++
		}
	}
	if n != 3 {
		t.Fatalf("assistant message replayed with %d tool_use blocks, want 3", n)
	}
}

func TestHiddenMaxParallelBoundsConcurrency(t *testing.T) {
	uses := []toolUse{}
	for _, id := range []string{"t1", "t2", "t3", "t4", "t5", "t6"} {
		uses = append(uses, toolUse{"toolu_" + id, "probe", `{}`})
	}
	f := newFake(t, toolTurn(1, 1, "", uses...), finalTurn(1, 1, "ok"))
	var cur, peak int32
	probe := Tool{Name: "probe", Description: "p", Handler: func(ctx context.Context, _ json.RawMessage) (string, error) {
		n := atomic.AddInt32(&cur, 1)
		for {
			p := atomic.LoadInt32(&peak)
			if n <= p || atomic.CompareAndSwapInt32(&peak, p, n) {
				break
			}
		}
		time.Sleep(40 * time.Millisecond)
		atomic.AddInt32(&cur, -1)
		return "ok", nil
	}}
	cfg := testConfig()
	cfg.MaxParallel = 2
	a := mustNew(t, f, cfg, probe)
	if _, err := a.Run(context.Background(), "x"); err != nil {
		t.Fatal(err)
	}
	if p := atomic.LoadInt32(&peak); p > 2 || p < 2 {
		t.Fatalf("peak concurrency = %d, want exactly MaxParallel=2", p)
	}
}

func TestHiddenUnknownToolIsErrorAndLoopRecovers(t *testing.T) {
	f := newFake(t,
		toolTurn(1, 1, "", toolUse{"toolu_x", "delete_namespace", `{"name":"shop"}`}),
		finalTurn(1, 1, "I cannot do that."),
	)
	a := mustNew(t, f, testConfig(), metricsTool())
	if _, err := a.Run(context.Background(), "x"); err != nil {
		t.Fatalf("an unknown tool is the model's mistake, not a Run error: %v", err)
	}
	b := lastUser(t, f.requests()[1])
	if len(b) != 1 || !b[0].IsError || b[0].ToolUseID != "toolu_x" {
		t.Fatalf("want one is_error tool_result for toolu_x, got %+v", b)
	}
	if !strings.Contains(b[0].resultText(), "query_metrics") {
		t.Fatalf("error should list the available tools so the model can recover: %q", b[0].resultText())
	}
}

func TestHiddenInvalidInputIsErrorNotHandlerCall(t *testing.T) {
	f := newFake(t,
		toolTurn(1, 1, "",
			toolUse{"toolu_1", "get_pod_events", `{"namespace":"shop"}`},
			toolUse{"toolu_2", "get_pod_events", `{"namespace":"shop","pod":null}`},
		),
		finalTurn(1, 1, "retrying"),
	)
	var calls []string
	a := mustNew(t, f, testConfig(), podEventsTool(&calls))
	if _, err := a.Run(context.Background(), "x"); err != nil {
		t.Fatal(err)
	}
	if len(calls) != 0 {
		t.Fatalf("handler ran with invalid input: %v", calls)
	}
	for _, b := range lastUser(t, f.requests()[1]) {
		if !b.IsError || !strings.Contains(b.resultText(), "pod") {
			t.Fatalf("want is_error naming the missing field 'pod', got %+v (%q)", b, b.resultText())
		}
	}
}

func TestHiddenHandlerErrorPanicAndTimeoutAreIsError(t *testing.T) {
	f := newFake(t,
		toolTurn(1, 1, "",
			toolUse{"toolu_err", "flaky", `{}`},
			toolUse{"toolu_panic", "buggy", `{}`},
			toolUse{"toolu_slow", "hang", `{}`},
		),
		finalTurn(1, 1, "partial data"),
	)
	flaky := Tool{Name: "flaky", Description: "d", Handler: func(context.Context, json.RawMessage) (string, error) {
		return "", errors.New("prometheus: 503 Service Unavailable")
	}}
	buggy := Tool{Name: "buggy", Description: "d", Handler: func(context.Context, json.RawMessage) (string, error) {
		var m map[string]int
		m["boom"]++ // nil map write: panics
		return "", nil
	}}
	hang := Tool{Name: "hang", Description: "d", Handler: func(ctx context.Context, _ json.RawMessage) (string, error) {
		<-ctx.Done()
		return "", ctx.Err()
	}}
	cfg := testConfig()
	cfg.ToolTimeout = 150 * time.Millisecond
	a := mustNew(t, f, cfg, flaky, buggy, hang)
	start := time.Now()
	if _, err := a.Run(context.Background(), "x"); err != nil {
		t.Fatalf("tool failures must go back to the model, not fail Run: %v", err)
	}
	if time.Since(start) > 2*time.Second {
		t.Fatal("ToolTimeout not applied to the hanging tool")
	}
	b := lastUser(t, f.requests()[1])
	if len(b) != 3 {
		t.Fatalf("want 3 results, got %d", len(b))
	}
	for _, x := range b {
		if !x.IsError {
			t.Fatalf("%s: want is_error=true", x.ToolUseID)
		}
	}
	if !strings.Contains(b[0].resultText(), "503") {
		t.Fatalf("handler error text should reach the model: %q", b[0].resultText())
	}
}

func TestHiddenMaxTurnsTypedError(t *testing.T) {
	loop := toolTurn(10, 1, "", toolUse{"toolu_l", "query_metrics", `{"promql":"up"}`})
	f := newFake(t, loop, loop, loop, loop, loop, loop)
	cfg := testConfig()
	cfg.MaxTurns = 3
	a := mustNew(t, f, cfg, metricsTool())
	res, err := a.Run(context.Background(), "x")
	var mt *MaxTurnsError
	if !errors.As(err, &mt) {
		t.Fatalf("want *MaxTurnsError, got %v", err)
	}
	if mt.Turns != 3 || res.Turns != 3 || len(f.requests()) != 3 {
		t.Fatalf("MaxTurns=3: err.Turns=%d res.Turns=%d api calls=%d, want 3/3/3", mt.Turns, res.Turns, len(f.requests()))
	}
	if res.Usage.InputTokens != 30 {
		t.Fatalf("partial Result must still carry usage: %+v", res.Usage)
	}
}

func TestHiddenUsageAndTranscriptAccumulate(t *testing.T) {
	f := newFake(t,
		toolTurn(100, 10, "", toolUse{"toolu_1", "query_metrics", `{"promql":"up"}`}),
		toolTurn(200, 20, "", toolUse{"toolu_2", "query_metrics", `{"promql":"rate(x[5m])"}`}),
		finalTurn(300, 30, "line one"),
	)
	a := mustNew(t, f, testConfig(), metricsTool())
	res, err := a.Run(context.Background(), "x")
	if err != nil {
		t.Fatal(err)
	}
	if res.Usage.InputTokens != 600 || res.Usage.OutputTokens != 60 {
		t.Fatalf("Usage = %+v, want 600/60", res.Usage)
	}
	if res.Turns != 3 || res.ToolCalls != 2 || res.StopReason != anthropic.StopReasonEndTurn {
		t.Fatalf("Turns=%d ToolCalls=%d StopReason=%q", res.Turns, res.ToolCalls, res.StopReason)
	}
	// user, assistant, user(results), assistant, user(results), assistant
	if len(res.Messages) != 6 {
		t.Fatalf("transcript has %d messages, want 6", len(res.Messages))
	}
	if n := len(f.requests()[2].Messages); n != 5 {
		t.Fatalf("third request sent %d messages, want the full history (5)", n)
	}
}

func TestHiddenMaxTokensAndRefusal(t *testing.T) {
	f := newFake(t, msgJSON("max_tokens", 5, 1024, textBlock("The root cause is")))
	a := mustNew(t, f, testConfig(), metricsTool())
	res, err := a.Run(context.Background(), "x")
	if !errors.Is(err, ErrMaxTokens) {
		t.Fatalf("want ErrMaxTokens, got %v", err)
	}
	if res.Text != "The root cause is" {
		t.Fatalf("truncated text should still be returned, got %q", res.Text)
	}

	f2 := newFake(t, msgJSON("refusal", 5, 3, textBlock("I can't help with that.")))
	a2 := mustNew(t, f2, testConfig(), metricsTool())
	if _, err := a2.Run(context.Background(), "x"); !errors.Is(err, ErrRefusal) {
		t.Fatalf("want ErrRefusal, got %v", err)
	}
}

func TestHiddenAPIErrorIsWrapped(t *testing.T) {
	f := newFake(t, step{status: 529, body: `{"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}`})
	a := mustNew(t, f, testConfig(), metricsTool())
	_, err := a.Run(context.Background(), "x")
	var apiErr *anthropic.Error
	if !errors.As(err, &apiErr) || apiErr.StatusCode != 529 {
		t.Fatalf("want a wrapped *anthropic.Error with status 529, got %v", err)
	}
}

func TestHiddenContextCancelDuringToolStopsLoop(t *testing.T) {
	f := newFake(t,
		toolTurn(1, 1, "", toolUse{"toolu_1", "hang", `{}`}),
		finalTurn(1, 1, "should never be requested"),
	)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	hang := Tool{Name: "hang", Description: "d", Handler: func(c context.Context, _ json.RawMessage) (string, error) {
		cancel() // the pod gets SIGTERM while a tool runs
		<-c.Done()
		return "", c.Err()
	}}
	a := mustNew(t, f, testConfig(), hang)
	_, err := a.Run(ctx, "x")
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("want error wrapping context.Canceled, got %v", err)
	}
	if n := len(f.requests()); n != 1 {
		t.Fatalf("made %d API calls; a cancelled run must not call the API again", n)
	}
}

func TestHiddenConcurrentRunsAreIndependent(t *testing.T) {
	steps := []step{}
	for i := 0; i < 8; i++ {
		steps = append(steps, finalTurn(1, 1, "ok"))
	}
	f := newFake(t, steps...)
	a := mustNew(t, f, testConfig(), metricsTool())
	var wg sync.WaitGroup
	for i := 0; i < 8; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			res, err := a.Run(context.Background(), "x")
			if err != nil || len(res.Messages) != 2 {
				t.Errorf("concurrent Run: err=%v messages=%d", err, len(res.Messages))
			}
		}()
	}
	wg.Wait()
	for i, r := range f.requests() {
		if len(r.Messages) != 1 {
			t.Fatalf("request %d carried %d messages: transcripts leak between runs", i, len(r.Messages))
		}
	}
}

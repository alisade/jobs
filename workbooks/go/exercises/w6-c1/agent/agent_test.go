package agent

import (
	"context"
	"encoding/json"
	"strings"
	"testing"
	"time"
)

// Test tools shared by the visible and hidden tests.

func podEventsTool(calls *[]string) Tool {
	return Tool{
		Name:        "get_pod_events",
		Description: "Recent Kubernetes events for a pod. Read-only.",
		Properties: map[string]any{
			"namespace": map[string]any{"type": "string"},
			"pod":       map[string]any{"type": "string"},
		},
		Required: []string{"namespace", "pod"},
		Handler: func(ctx context.Context, in json.RawMessage) (string, error) {
			var args struct{ Namespace, Pod string }
			if err := json.Unmarshal(in, &args); err != nil {
				return "", err
			}
			if calls != nil {
				*calls = append(*calls, args.Namespace+"/"+args.Pod)
			}
			return "Warning BackOff Back-off restarting failed container (x14 over 6m)", nil
		},
	}
}

func metricsTool() Tool {
	return Tool{
		Name:        "query_metrics",
		Description: "Run a PromQL instant query. Read-only.",
		Properties:  map[string]any{"promql": map[string]any{"type": "string"}},
		Required:    []string{"promql"},
		Handler: func(ctx context.Context, in json.RawMessage) (string, error) {
			return `[{"metric":{"pod":"checkout-7d9f"},"value":"0.97"}]`, nil
		},
	}
}

func testConfig() Config {
	return Config{MaxTokens: 1024, MaxTurns: 5, System: "You are the Kestrel incident triage agent.", ToolTimeout: 2 * time.Second}
}

// Visible test: one tool call, then a final answer.
func TestRunSingleToolCallThenAnswer(t *testing.T) {
	f := newFake(t,
		toolTurn(100, 20, "Checking pod events.", toolUse{"toolu_01", "get_pod_events", `{"namespace":"shop","pod":"checkout-7d9f"}`}),
		finalTurn(180, 40, "checkout-7d9f is crash-looping: back-off restarting."),
	)
	var calls []string
	a, err := New(f.client(), testConfig(), podEventsTool(&calls), metricsTool())
	if err != nil {
		t.Fatalf("New: %v", err)
	}
	res, err := a.Run(context.Background(), "Why is checkout paging?")
	if err != nil {
		t.Fatalf("Run: %v", err)
	}
	if !strings.Contains(res.Text, "crash-looping") {
		t.Fatalf("Text = %q", res.Text)
	}
	if res.Turns != 2 {
		t.Fatalf("Turns = %d, want 2", res.Turns)
	}
	if len(calls) != 1 || calls[0] != "shop/checkout-7d9f" {
		t.Fatalf("tool calls = %v", calls)
	}
	reqs := f.requests()
	if len(reqs) != 2 {
		t.Fatalf("API calls = %d, want 2", len(reqs))
	}
	last := reqs[1].Messages[len(reqs[1].Messages)-1]
	if last.Role != "user" || len(last.Content) != 1 || last.Content[0].Type != "tool_result" || last.Content[0].ToolUseID != "toolu_01" {
		t.Fatalf("second request must end with a user tool_result for toolu_01, got %+v", last)
	}
}

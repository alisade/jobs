// Command triage runs the incident-triage agent once against the real Claude API.
// It is only used by the optional `make live` target (needs ANTHROPIC_API_KEY and
// costs money). Tests and grading never run it.
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/anthropics/anthropic-sdk-go"

	"github.com/kestrel-platform/triage-agent/agent"
)

func main() {
	if os.Getenv("ANTHROPIC_API_KEY") == "" {
		fmt.Fprintln(os.Stderr, "ANTHROPIC_API_KEY is not set; `make live` is optional and calls a paid API")
		os.Exit(2)
	}
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGTERM, os.Interrupt)
	defer stop()

	events := agent.Tool{
		Name:        "get_pod_events",
		Description: "Recent Kubernetes events for one pod. Read-only. Use before guessing at a crash cause.",
		Properties: map[string]any{
			"namespace": map[string]any{"type": "string", "description": "Kubernetes namespace"},
			"pod":       map[string]any{"type": "string", "description": "Pod name"},
		},
		Required: []string{"namespace", "pod"},
		Handler: func(ctx context.Context, in json.RawMessage) (string, error) {
			return "Warning OOMKilled container checkout exceeded memory limit 512Mi (x6 over 20m)", nil
		},
	}
	metrics := agent.Tool{
		Name:        "query_metrics",
		Description: "Run a PromQL instant query against the platform Prometheus. Read-only.",
		Properties:  map[string]any{"promql": map[string]any{"type": "string"}},
		Required:    []string{"promql"},
		Handler: func(ctx context.Context, in json.RawMessage) (string, error) {
			return `[{"metric":{"pod":"checkout-7d9f"},"value":"0.99"}]`, nil
		},
	}

	a, err := agent.New(anthropic.NewClient(), agent.Config{
		System: "You are the Kestrel platform incident triage agent. Use tools to gather evidence, then give a short root-cause hypothesis.",
	}, events, metrics)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	res, err := a.Run(ctx, "checkout in namespace shop is paging for 5xx. Pod checkout-7d9f. What is going on?")
	fmt.Printf("%s\n\nturns=%d tool_calls=%d usage=%+v err=%v\n", res.Text, res.Turns, res.ToolCalls, res.Usage, err)
}

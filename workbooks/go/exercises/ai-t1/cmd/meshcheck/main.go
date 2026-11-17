// Command meshcheck replays MCP calls against the offline mesh model and prints
// what the k8s-tools sidecar would log. Run: go run ./cmd/meshcheck
package main

import (
	"fmt"
	"os"

	"github.com/kestrelbank/mesh-config/meshsim"
)

func main() {
	c, err := meshsim.Load(".")
	if err != nil {
		fmt.Fprintln(os.Stderr, "load:", err)
		os.Exit(2)
	}
	dst, err := c.ServiceWorkload("mcp-tools", "k8s-tools")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	agent, _ := c.FromDeployment("agents", "agent-runtime")
	eval, _ := c.FromDeployment("agents", "eval-runner")
	batch := c.Pod("batch", "spark", map[string]string{"app": "spark-driver"})

	fmt.Printf("server k8s-tools: sidecar=%v\n\n", dst.Sidecar)
	fmt.Printf("%-28s %-8s %-7s %-14s %s\n", "CALLER", "SIDECAR", "METHOD", "PATH", "RESULT")
	for _, tc := range []struct {
		name         string
		w            meshsim.Workload
		method, path string
	}{
		{"agents/agent-runtime", agent, "POST", "/mcp"},
		{"agents/agent-runtime", agent, "GET", "/mcp"},
		{"agents/agent-runtime", agent, "POST", "/admin/reload"},
		{"agents/eval-runner", eval, "POST", "/mcp"},
		{"batch/spark-driver", batch, "POST", "/mcp"},
	} {
		fmt.Printf("%-28s %-8v %-7s %-14s %s\n", tc.name, tc.w.Sidecar, tc.method, tc.path, c.Call(tc.w, dst, tc.method, tc.path))
	}
}

// Command plan-gate checks a Terraform JSON plan against a policy for CI.
//
//	terraform show -json plan.out > plan.json
//	plan-gate -plan plan.json -policy policy.json [-json]
//
// Exit codes: 0 pass, 1 policy violation, 2 usage or parse error.
package main

import (
	"os"

	"tessellate.example/plan-gate/gate"
)

func main() {
	os.Exit(gate.Run(os.Args[1:], os.Stdout, os.Stderr))
}

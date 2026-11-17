package gate

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"strings"
)

// Exit codes.
const (
	ExitPass      = 0
	ExitViolation = 1
	ExitUsage     = 2
)

// ChangeReport is one resource in the JSON report.
type ChangeReport struct {
	Address      string       `json:"address"`
	Action       Action       `json:"action"`
	Importing    bool         `json:"importing"`
	ActionReason string       `json:"action_reason,omitempty"`
	ReplacePaths []string     `json:"replace_paths,omitempty"` // each path joined with "."
	Attributes   []AttrChange `json:"changed_attributes,omitempty"`
}

// Report is the --json output.
type Report struct {
	Summary    Summary        `json:"summary"`
	Changes    []ChangeReport `json:"changes"`
	Violations []Violation    `json:"violations"`
	Result     string         `json:"result"` // "pass" or "fail"
}

// Run is the CLI: plan-gate -plan plan.json [-policy policy.json] [-json].
// Exit 0 when the plan passes, 1 on any policy violation, 2 on usage, read, decode or
// validation errors (message on stderr, nothing on stdout).
func Run(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("plan-gate", flag.ContinueOnError)
	fs.SetOutput(stderr)
	planPath := fs.String("plan", "", "path to `terraform show -json` output (required)")
	policyPath := fs.String("policy", "", "path to a policy JSON file (optional)")
	asJSON := fs.Bool("json", false, "print a JSON report instead of text")
	if err := fs.Parse(args); err != nil {
		return ExitUsage
	}
	// TODO: require -plan, validate the plan, load the policy, and return the right exit code.
	plan, _ := LoadPlan(*planPath)
	_ = policyPath
	rep := Build(plan, Policy{})
	if *asJSON {
		enc := json.NewEncoder(stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(rep)
	} else {
		WriteText(stdout, rep)
	}
	return ExitPass
}

// Build assembles the report: Summary, Violations (never nil: use an empty slice), Changes
// sorted by address (leave out no-op and read entries that are not imports; include
// changed_attributes for update and replace), and Result "pass" or "fail".
func Build(plan Plan, pol Policy) Report {
	// TODO: implement.
	return Report{Summary: Summarize(plan), Changes: []ChangeReport{}, Violations: []Violation{}, Result: "pass"}
}

var symbols = map[Action]string{ActCreate: "+", ActUpdate: "~", ActDelete: "-", ActReplace: "-/+", ActNoOp: "=", ActRead: "<="}

// WriteText prints the human report. You should not need to change it.
func WriteText(w io.Writer, rep Report) {
	fmt.Fprintln(w, SummaryLine(rep.Summary))
	for _, c := range rep.Changes {
		tag := ""
		if c.Importing {
			tag = " (import)"
		}
		fmt.Fprintf(w, "  %-3s %s%s\n", symbols[c.Action], c.Address, tag)
		if c.ActionReason != "" {
			fmt.Fprintf(w, "        reason: %s\n", c.ActionReason)
		}
		for _, p := range c.ReplacePaths {
			fmt.Fprintf(w, "        forces replacement: %s\n", p)
		}
		for _, a := range c.Attributes {
			fmt.Fprintf(w, "        %s: %s -> %s\n", a.Name, a.Before, a.After)
		}
	}
	for _, v := range rep.Violations {
		fmt.Fprintf(w, "VIOLATION %s [%s] %s\n", v.Address, v.Rule, v.Message)
	}
	fmt.Fprintf(w, "RESULT: %s\n", strings.ToUpper(rep.Result))
}

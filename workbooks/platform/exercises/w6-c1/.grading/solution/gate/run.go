package gate

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"sort"
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
	ReplacePaths []string     `json:"replace_paths,omitempty"`
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
func Run(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("plan-gate", flag.ContinueOnError)
	fs.SetOutput(stderr)
	planPath := fs.String("plan", "", "path to `terraform show -json` output (required)")
	policyPath := fs.String("policy", "", "path to a policy JSON file (optional)")
	asJSON := fs.Bool("json", false, "print a JSON report instead of text")
	if err := fs.Parse(args); err != nil {
		return ExitUsage
	}
	if *planPath == "" {
		fmt.Fprintln(stderr, "plan-gate: -plan is required")
		return ExitUsage
	}
	plan, err := LoadPlan(*planPath)
	if err != nil {
		fmt.Fprintf(stderr, "plan-gate: %v\n", err)
		return ExitUsage
	}
	if err := Validate(plan); err != nil {
		fmt.Fprintf(stderr, "plan-gate: %v\n", err)
		return ExitUsage
	}
	var pol Policy
	if *policyPath != "" {
		if pol, err = LoadPolicy(*policyPath); err != nil {
			fmt.Fprintf(stderr, "plan-gate: %v\n", err)
			return ExitUsage
		}
	}
	rep := Build(plan, pol)
	if *asJSON {
		enc := json.NewEncoder(stdout)
		enc.SetIndent("", "  ")
		if err := enc.Encode(rep); err != nil {
			return ExitUsage
		}
	} else {
		WriteText(stdout, rep)
	}
	if rep.Result == "fail" {
		return ExitViolation
	}
	return ExitPass
}

// Build assembles the report. Changes are sorted by address; no-op and read entries that are
// not imports are left out.
func Build(plan Plan, pol Policy) Report {
	rep := Report{Summary: Summarize(plan), Changes: []ChangeReport{}, Violations: Evaluate(plan, pol)}
	if rep.Violations == nil {
		rep.Violations = []Violation{}
	}
	for _, rc := range plan.ResourceChanges {
		act, _ := Classify(rc)
		imp := rc.Change.Importing != nil
		if (act == ActNoOp || act == ActRead) && !imp {
			continue
		}
		cr := ChangeReport{Address: rc.Address, Action: act, Importing: imp, ActionReason: rc.ActionReason}
		for _, p := range rc.Change.ReplacePaths {
			parts := make([]string, len(p))
			for i, e := range p {
				parts[i] = fmt.Sprint(e)
			}
			cr.ReplacePaths = append(cr.ReplacePaths, strings.Join(parts, "."))
		}
		if act == ActUpdate || act == ActReplace {
			cr.Attributes = ChangedAttributes(rc)
		}
		rep.Changes = append(rep.Changes, cr)
	}
	sort.Slice(rep.Changes, func(i, j int) bool { return rep.Changes[i].Address < rep.Changes[j].Address })
	rep.Result = "pass"
	if len(rep.Violations) > 0 {
		rep.Result = "fail"
	}
	return rep
}

var symbols = map[Action]string{ActCreate: "+", ActUpdate: "~", ActDelete: "-", ActReplace: "-/+", ActNoOp: "=", ActRead: "<="}

// WriteText prints the human report.
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

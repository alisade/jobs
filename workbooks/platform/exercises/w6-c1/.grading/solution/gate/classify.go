package gate

import (
	"fmt"
	"strings"
)

// Classify maps a change's actions to one Action. Unknown combinations are an error.
func Classify(rc ResourceChange) (Action, error) {
	a := rc.Change.Actions
	switch strings.Join(a, ",") {
	case "no-op":
		return ActNoOp, nil
	case "create":
		return ActCreate, nil
	case "read":
		return ActRead, nil
	case "update":
		return ActUpdate, nil
	case "delete":
		return ActDelete, nil
	case "delete,create", "create,delete":
		return ActReplace, nil
	}
	return "", fmt.Errorf("%s: unknown actions %v", rc.Address, a)
}

// Validate checks the plan format: format_version major 1, and every action known.
func Validate(p Plan) error {
	if p.FormatVersion == "" {
		return fmt.Errorf("not a Terraform JSON plan: format_version missing")
	}
	if major, _, _ := strings.Cut(p.FormatVersion, "."); major != "1" {
		return fmt.Errorf("unsupported format_version %q (want 1.x)", p.FormatVersion)
	}
	for _, rc := range p.ResourceChanges {
		if _, err := Classify(rc); err != nil {
			return err
		}
	}
	return nil
}

// Summarize counts the plan like terraform does. Call Validate first.
func Summarize(p Plan) Summary {
	var s Summary
	for _, rc := range p.ResourceChanges {
		if rc.Mode == "data" {
			continue
		}
		if rc.Change.Importing != nil {
			s.Import++
		}
		act, _ := Classify(rc)
		switch act {
		case ActCreate:
			s.Add++
		case ActUpdate:
			s.Change++
		case ActDelete:
			s.Destroy++
		case ActReplace:
			s.Add++
			s.Destroy++
			s.Replace++
		}
	}
	return s
}

// SummaryLine renders the summary like the last line of terraform plan.
func SummaryLine(s Summary) string {
	line := fmt.Sprintf("Plan: %d to import, %d to add, %d to change, %d to destroy.", s.Import, s.Add, s.Change, s.Destroy)
	if s.Replace > 0 {
		line += fmt.Sprintf(" (%d replacement(s))", s.Replace)
	}
	return line
}

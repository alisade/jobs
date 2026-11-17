package gate

import "fmt"

// Classify maps a change's actions to one Action:
//
//	["no-op"] no-op, ["create"] create, ["read"] read, ["update"] update, ["delete"] delete,
//	["delete","create"] and ["create","delete"] replace. Anything else is an error.
func Classify(rc ResourceChange) (Action, error) {
	// TODO: implement.
	return ActNoOp, nil
}

// Validate checks the plan format before anything else runs: format_version must be present
// and its major version must be 1, and every resource change must have a known action set.
func Validate(p Plan) error {
	// TODO: implement.
	return nil
}

// Summarize counts the plan like terraform does (see Summary). Imports are counted from
// Change.Importing, independent of the action. Data sources are not counted.
func Summarize(p Plan) Summary {
	// TODO: implement.
	return Summary{}
}

// SummaryLine renders the summary like the last line of terraform plan.
func SummaryLine(s Summary) string {
	line := fmt.Sprintf("Plan: %d to import, %d to add, %d to change, %d to destroy.", s.Import, s.Add, s.Change, s.Destroy)
	if s.Replace > 0 {
		line += fmt.Sprintf(" (%d replacement(s))", s.Replace)
	}
	return line
}

package gate

import (
	"fmt"
	"slices"
	"sort"
)

// Evaluate returns the policy violations in the plan, sorted by address then rule.
func Evaluate(p Plan, pol Policy) []Violation {
	var out []Violation
	for _, rc := range p.ResourceChanges {
		if rc.Mode == "data" {
			continue
		}
		act, err := Classify(rc)
		if err != nil {
			out = append(out, Violation{rc.Address, "unknown_action", err.Error()})
			continue
		}
		if (act == ActDelete || act == ActReplace) && slices.Contains(pol.ProtectedTypes, rc.Type) {
			out = append(out, Violation{rc.Address, "protected_type",
				fmt.Sprintf("%s is a protected type and must not be %sd%s", rc.Type, verb(act), reason(rc))})
		}
		if !pol.ImportsOnly {
			continue
		}
		switch act {
		case ActCreate, ActDelete, ActReplace:
			out = append(out, Violation{rc.Address, "imports_only_action",
				fmt.Sprintf("imports-only plan must not %s resources%s", act, reason(rc))})
		case ActUpdate:
			for _, ch := range ChangedAttributes(rc) {
				if !slices.Contains(pol.AllowedUpdateAttributes, ch.Name) {
					out = append(out, Violation{rc.Address, "imports_only_attribute",
						fmt.Sprintf("imports-only plan may not change %q", ch.Name)})
				}
			}
		}
	}
	sort.SliceStable(out, func(i, j int) bool {
		if out[i].Address != out[j].Address {
			return out[i].Address < out[j].Address
		}
		return out[i].Rule < out[j].Rule
	})
	return out
}

func verb(a Action) string {
	if a == ActReplace {
		return "replace"
	}
	return "delete"
}

func reason(rc ResourceChange) string {
	if rc.ActionReason != "" {
		return " (" + rc.ActionReason + ")"
	}
	return ""
}

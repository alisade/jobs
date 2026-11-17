package gate

// Evaluate returns the policy violations in the plan, sorted by address then rule. Data
// sources never violate. Rules:
//   - protected_type: a resource whose Type is in ProtectedTypes is deleted or replaced.
//   - imports_only_action (ImportsOnly only): any create, delete or replace.
//   - imports_only_attribute (ImportsOnly only): an update that changes an attribute not in
//     AllowedUpdateAttributes (one violation per attribute).
//
// Messages should say what happened and include the action_reason when there is one.
func Evaluate(p Plan, pol Policy) []Violation {
	// TODO: implement.
	return nil
}

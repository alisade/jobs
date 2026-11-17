// Package gate reads Terraform plan JSON (the output of `terraform show -json plan.out`),
// summarizes it, checks it against a policy and renders a report for CI.
package gate

import (
	"encoding/json"
	"fmt"
	"os"
)

// You should not need to change this file. Write your code in classify.go, diff.go, policy.go
// and run.go.

// Plan is the subset of the Terraform JSON plan format this tool reads.
// Format reference: https://developer.hashicorp.com/terraform/internals/json-format
type Plan struct {
	FormatVersion    string           `json:"format_version"`
	TerraformVersion string           `json:"terraform_version"`
	ResourceChanges  []ResourceChange `json:"resource_changes"`
}

// ResourceChange is one entry of resource_changes.
type ResourceChange struct {
	Address      string `json:"address"`
	Mode         string `json:"mode"` // "managed" or "data"
	Type         string `json:"type"`
	Name         string `json:"name"`
	ProviderName string `json:"provider_name"`
	Change       Change `json:"change"`
	// ActionReason explains some actions, e.g. "replace_because_cannot_update",
	// "replace_because_tainted", "delete_because_no_resource_config".
	ActionReason string `json:"action_reason,omitempty"`
}

// Change is the planned change of one resource instance.
type Change struct {
	// Actions is one of: ["no-op"], ["create"], ["read"], ["update"], ["delete"],
	// ["delete","create"] (replace, destroy first) or ["create","delete"]
	// (replace, create_before_destroy).
	Actions []string `json:"actions"`
	Before  any      `json:"before"`
	After   any      `json:"after"`
	// BeforeSensitive / AfterSensitive mirror the shape of Before / After. A value of true at
	// some position means the value there is sensitive. They may be false or absent.
	BeforeSensitive any `json:"before_sensitive"`
	AfterSensitive  any `json:"after_sensitive"`
	// Importing is set when this change imports an existing object (import block).
	Importing *Importing `json:"importing,omitempty"`
	// ReplacePaths lists the attribute paths that force replacement, e.g. [["auto_create_subnetworks"]].
	ReplacePaths [][]any `json:"replace_paths,omitempty"`
}

// Importing describes an import of an existing object.
type Importing struct {
	ID string `json:"id"`
}

// Policy is the gate configuration (policy JSON file).
type Policy struct {
	// ProtectedTypes may never be deleted or replaced (any mode).
	ProtectedTypes []string `json:"protected_types"`
	// ImportsOnly is for migration pull requests: nothing may be created, deleted or replaced,
	// and in-place updates may only touch AllowedUpdateAttributes.
	ImportsOnly bool `json:"imports_only"`
	// AllowedUpdateAttributes are the top-level attributes an update may change in
	// imports-only mode (for example labels that the provider normalizes).
	AllowedUpdateAttributes []string `json:"allowed_update_attributes"`
}

// Action is the classified action of a resource change.
type Action string

const (
	ActNoOp    Action = "no-op"
	ActCreate  Action = "create"
	ActRead    Action = "read"
	ActUpdate  Action = "update"
	ActDelete  Action = "delete"
	ActReplace Action = "replace"
)

// Summary counts changes the way `terraform plan` prints them: a replacement counts once in Add,
// once in Destroy and once in Replace. Data sources (mode "data") are not counted.
type Summary struct {
	Import  int `json:"import"`
	Add     int `json:"add"`
	Change  int `json:"change"`
	Destroy int `json:"destroy"`
	Replace int `json:"replace"`
}

// AttrChange is one changed top-level attribute, with values rendered as compact JSON or the
// literal "(sensitive value)".
type AttrChange struct {
	Name   string `json:"name"`
	Before string `json:"before"`
	After  string `json:"after"`
}

// Violation is one policy failure.
type Violation struct {
	Address string `json:"address"`
	Rule    string `json:"rule"` // "protected_type", "imports_only_action" or "imports_only_attribute"
	Message string `json:"message"`
}

// Sensitive is the placeholder printed instead of a sensitive value.
const Sensitive = "(sensitive value)"

// LoadPlan reads and decodes a plan JSON file. It does not validate the content.
func LoadPlan(path string) (Plan, error) {
	var p Plan
	b, err := os.ReadFile(path)
	if err != nil {
		return p, err
	}
	if err := json.Unmarshal(b, &p); err != nil {
		return p, fmt.Errorf("decode %s: %w", path, err)
	}
	return p, nil
}

// LoadPolicy reads and decodes a policy JSON file.
func LoadPolicy(path string) (Policy, error) {
	var p Policy
	b, err := os.ReadFile(path)
	if err != nil {
		return p, err
	}
	if err := json.Unmarshal(b, &p); err != nil {
		return p, fmt.Errorf("decode %s: %w", path, err)
	}
	return p, nil
}

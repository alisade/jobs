package fn

import (
	"context"
	"fmt"
	"strings"
)

// Reconcile composes the XR, applies what changed, prunes what is no longer desired and
// writes the XR conditions. It returns the XR with its new conditions.
func Reconcile(ctx context.Context, c Client, xr XR) (XR, error) {
	res := Compose(xr)
	if res.Fatal != "" {
		xr.Conditions = SetCondition(xr.Conditions, Condition{Type: "Synced", Status: "False", Reason: "ComposeFailed", Message: res.Fatal})
		xr.Conditions = SetCondition(xr.Conditions, Condition{Type: "Ready", Status: "False", Reason: "ComposeFailed", Message: res.Fatal})
		return xr, c.UpdateXRStatus(ctx, xr)
	}
	fail := func(err error) (XR, error) {
		xr.Conditions = SetCondition(xr.Conditions, Condition{Type: "Synced", Status: "False", Reason: "ReconcileError", Message: err.Error()})
		_ = c.UpdateXRStatus(ctx, xr)
		return xr, err
	}
	existing, err := c.List(ctx, xr.Metadata.Namespace, map[string]string{LabelComposite: xr.Metadata.Name})
	if err != nil {
		return fail(fmt.Errorf("list composed resources: %w", err))
	}
	have := map[string]Resource{}
	for _, r := range existing {
		if r.Metadata.Namespace != xr.Metadata.Namespace {
			continue
		}
		have[r.Key()] = r
	}
	want := map[string]bool{}
	var notReady []string
	for _, d := range res.Desired {
		want[d.Key()] = true
		cur, ok := have[d.Key()]
		if !ok || !SameDesired(cur, d) {
			if err := c.Apply(ctx, d); err != nil {
				return fail(fmt.Errorf("apply %s: %w", d.Key(), err))
			}
		}
		if !ok || !IsReady(cur) {
			notReady = append(notReady, d.Key())
		}
	}
	for _, r := range existing {
		if r.Metadata.Namespace != xr.Metadata.Namespace || want[r.Key()] {
			continue
		}
		if err := c.Delete(ctx, r.Metadata.Namespace, r.Kind, r.Metadata.Name); err != nil {
			return fail(fmt.Errorf("delete %s: %w", r.Key(), err))
		}
	}
	xr.Conditions = SetCondition(xr.Conditions, Condition{Type: "Synced", Status: "True", Reason: "ReconcileSuccess"})
	if len(notReady) == 0 {
		xr.Conditions = SetCondition(xr.Conditions, Condition{Type: "Ready", Status: "True", Reason: "Available"})
	} else {
		xr.Conditions = SetCondition(xr.Conditions, Condition{Type: "Ready", Status: "False", Reason: "Creating",
			Message: "waiting for: " + strings.Join(notReady, ", ")})
	}
	return xr, c.UpdateXRStatus(ctx, xr)
}

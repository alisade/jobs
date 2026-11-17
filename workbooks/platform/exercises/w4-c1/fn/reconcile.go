package fn

import "context"

// Reconcile composes the XR, applies what changed, prunes what is no longer desired and
// writes the XR conditions (Synced, Ready). It returns the XR with its new conditions.
//
// See README.md ("Reconcile contract"). Key points:
//   - Fatal compose result: Synced=False and Ready=False with reason ComposeFailed and the
//     fatal message; write the status; return a nil error; touch no managed resources.
//   - List only this XR's composed resources, in this XR's namespace.
//   - Apply a desired resource only when it is missing or SameDesired says it differs, so a
//     second reconcile of an unchanged XR issues zero Apply/Delete calls.
//   - Delete composed resources that are no longer desired.
//   - Ready=True (reason Available) only when every desired resource exists and is Ready;
//     otherwise Ready=False, reason Creating, message "waiting for: Kind/name, Kind/name" in
//     desired order.
//   - A client error: Synced=False reason ReconcileError, write the status, return the error.
func Reconcile(ctx context.Context, c Client, xr XR) (XR, error) {
	// TODO: implement.
	res := Compose(xr)
	_ = res
	return xr, nil
}

package janitor

import (
	"context"
	"slices"
	"testing"

	"github.com/aws/aws-sdk-go-v2/service/ec2/types"
)

// Visible test: the happy path from the README. Run with `make test`.
func TestRunDeletesExpiredSnapshotsOldestFirst(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{
		snap("snap-new", 3, nil, "nightly"),
		snap("snap-old", 90, nil, "nightly"),
		snap("snap-mid", 45, nil, "nightly"),
	}}}
	res, err := Run(context.Background(), f, baseConfig())
	if err != nil {
		t.Fatalf("Run returned error: %v", err)
	}
	want := []string{"snap-old", "snap-mid"}
	if !slices.Equal(res.Deleted, want) {
		t.Fatalf("Deleted = %v, want %v (oldest first, young snapshots untouched)", res.Deleted, want)
	}
	if !slices.Equal(f.Deletes, want) {
		t.Fatalf("DeleteSnapshot calls = %v, want %v", f.Deletes, want)
	}
}

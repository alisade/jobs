package janitor

import (
	"context"
	"errors"
	"fmt"
	"slices"
	"testing"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ec2/types"
	"github.com/aws/smithy-go"
)

func apiErr(code string) error {
	// Wrap like the SDK does: operation error -> response error -> API error.
	return fmt.Errorf("operation error EC2: DeleteSnapshot, https response error StatusCode: 400: %w",
		&smithy.GenericAPIError{Code: code, Message: code + " message"})
}

func TestHiddenPaginatesAllPagesWithOwnerFilter(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{
		{snap("snap-a", 60, nil, "")},
		{snap("snap-b", 50, nil, "")},
		{snap("snap-c", 40, nil, "")},
	}}
	res, err := Run(context.Background(), f, baseConfig())
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(f.DescribeInputs) != 3 {
		t.Fatalf("DescribeSnapshots called %d times, want 3 (one per page)", len(f.DescribeInputs))
	}
	if got := f.DescribeInputs[0].OwnerIds; !slices.Equal(got, []string{"111122223333"}) {
		t.Fatalf("OwnerIds = %v, want [111122223333]: never list public/shared snapshots", got)
	}
	if !slices.Equal(res.Deleted, []string{"snap-a", "snap-b", "snap-c"}) {
		t.Fatalf("Deleted = %v", res.Deleted)
	}
}

func TestHiddenRetainTagCaseInsensitiveAndCustomKey(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{
		snap("snap-keep", 100, map[string]string{"retain": "TRUE"}, ""),
		snap("snap-false", 100, map[string]string{"retain": "false"}, ""),
		snap("snap-legal", 100, map[string]string{"legal-hold": "True"}, ""),
	}}}
	cfg := baseConfig()
	res, err := Run(context.Background(), f, cfg)
	if err != nil {
		t.Fatal(err)
	}
	if res.Skipped["snap-keep"] != ReasonRetained {
		t.Fatalf("snap-keep: Skipped reason = %q, want %q", res.Skipped["snap-keep"], ReasonRetained)
	}
	if !slices.Contains(res.Deleted, "snap-false") || !slices.Contains(res.Deleted, "snap-legal") {
		t.Fatalf("default keep tag is \"retain\"; Deleted = %v", res.Deleted)
	}

	f2 := &fakeEC2{Pages: [][]types.Snapshot{{snap("snap-legal", 100, map[string]string{"legal-hold": "True"}, "")}}}
	cfg.KeepTag = "legal-hold"
	res, err = Run(context.Background(), f2, cfg)
	if err != nil {
		t.Fatal(err)
	}
	if len(f2.Deletes) != 0 || res.Skipped["snap-legal"] != ReasonRetained {
		t.Fatalf("custom KeepTag ignored: deletes=%v skipped=%v", f2.Deletes, res.Skipped)
	}
}

func TestHiddenSkipsAMIBackedSnapshots(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{
		snap("snap-ami", 400, nil, "Created by CreateImage(i-0abc) for ami-0123 from vol-9"),
		snap("snap-plain", 400, nil, "Copied for DestinationAmi ami-1 Created by CreateImage("),
	}}}
	res, err := Run(context.Background(), f, baseConfig())
	if err != nil {
		t.Fatal(err)
	}
	if res.Skipped["snap-ami"] != ReasonAMI {
		t.Fatalf("snap-ami reason = %q, want %q", res.Skipped["snap-ami"], ReasonAMI)
	}
	if slices.Contains(f.Deletes, "snap-ami") {
		t.Fatal("deleted a snapshot that backs an AMI")
	}
	if !slices.Contains(res.Deleted, "snap-plain") {
		t.Fatal("only a description that STARTS with the CreateImage prefix marks an AMI snapshot")
	}
}

func TestHiddenRetentionBoundaryAndYoungIgnored(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{
		snap("snap-exact", 30, nil, ""), // exactly at cutoff: keep (Python uses >= cutoff to skip)
		snap("snap-31", 31, nil, ""),
		snap("snap-1", 1, nil, ""),
	}}}
	res, err := Run(context.Background(), f, baseConfig())
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(res.Deleted, []string{"snap-31"}) {
		t.Fatalf("Deleted = %v, want [snap-31]", res.Deleted)
	}
	if _, ok := res.Skipped["snap-1"]; ok {
		t.Fatal("young snapshots are ignored, not recorded as skipped")
	}
}

func TestHiddenDryRunCountsDryRunOperationAsDeleted(t *testing.T) {
	f := &fakeEC2{
		Pages:     [][]types.Snapshot{{snap("snap-a", 60, nil, ""), snap("snap-b", 70, nil, "")}},
		DeleteErr: map[string]error{"snap-a": apiErr("DryRunOperation"), "snap-b": apiErr("DryRunOperation")},
	}
	cfg := baseConfig()
	cfg.DryRun = true
	res, err := Run(context.Background(), f, cfg)
	if err != nil {
		t.Fatalf("DryRunOperation is success in dry-run mode, got error: %v", err)
	}
	if !slices.Equal(res.Deleted, []string{"snap-b", "snap-a"}) {
		t.Fatalf("Deleted = %v, want [snap-b snap-a]", res.Deleted)
	}
	for i, dr := range f.DeleteDryRun {
		if !dr {
			t.Fatalf("DeleteSnapshot call %d sent DryRun=false in dry-run mode", i)
		}
	}
	if len(res.Failed) != 0 {
		t.Fatalf("Failed = %v, want empty", res.Failed)
	}
}

func TestHiddenInUseIsSkipNotFailure(t *testing.T) {
	f := &fakeEC2{
		Pages:     [][]types.Snapshot{{snap("snap-busy", 60, nil, ""), snap("snap-ok", 50, nil, "")}},
		DeleteErr: map[string]error{"snap-busy": apiErr("InvalidSnapshot.InUse")},
	}
	res, err := Run(context.Background(), f, baseConfig())
	if err != nil {
		t.Fatalf("InvalidSnapshot.InUse must not fail the run: %v", err)
	}
	if res.Skipped["snap-busy"] != ReasonInUse {
		t.Fatalf("reason = %q, want %q", res.Skipped["snap-busy"], ReasonInUse)
	}
	if !slices.Equal(res.Deleted, []string{"snap-ok"}) {
		t.Fatalf("Deleted = %v", res.Deleted)
	}
}

func TestHiddenPartialFailureAggregatesAndContinues(t *testing.T) {
	throttle := apiErr("RequestLimitExceeded")
	denied := apiErr("UnauthorizedOperation")
	f := &fakeEC2{
		Pages: [][]types.Snapshot{{
			snap("snap-1", 90, nil, ""), snap("snap-2", 80, nil, ""), snap("snap-3", 70, nil, ""),
		}},
		DeleteErr: map[string]error{"snap-1": throttle, "snap-2": denied},
	}
	res, err := Run(context.Background(), f, baseConfig())
	if !errors.Is(err, ErrPartialFailure) {
		t.Fatalf("errors.Is(err, ErrPartialFailure) = false; err = %v", err)
	}
	if !errors.Is(err, throttle) || !errors.Is(err, denied) {
		t.Fatalf("returned error must wrap every underlying delete error; err = %v", err)
	}
	var ae smithy.APIError
	if !errors.As(err, &ae) {
		t.Fatal("errors.As(err, *smithy.APIError) should find the API error through the wrapping")
	}
	if !slices.Equal(res.Deleted, []string{"snap-3"}) {
		t.Fatalf("must continue after a failure; Deleted = %v", res.Deleted)
	}
	if len(res.Failed) != 2 || res.Failed["snap-1"] == nil || res.Failed["snap-2"] == nil {
		t.Fatalf("Failed = %v", res.Failed)
	}
}

func TestHiddenMaxDeletesCap(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{
		snap("snap-1", 90, nil, ""), snap("snap-2", 80, nil, ""), snap("snap-3", 70, nil, ""), snap("snap-4", 60, nil, ""),
	}}}
	cfg := baseConfig()
	cfg.MaxDeletes = 2
	res, err := Run(context.Background(), f, cfg)
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(f.Deletes, []string{"snap-1", "snap-2"}) {
		t.Fatalf("DeleteSnapshot calls = %v, want the 2 oldest", f.Deletes)
	}
	if res.Skipped["snap-3"] != ReasonMaxDeletes || res.Skipped["snap-4"] != ReasonMaxDeletes {
		t.Fatalf("Skipped = %v, want snap-3 and snap-4 as %q", res.Skipped, ReasonMaxDeletes)
	}
}

func TestHiddenMaxDeletesCountsOnlySuccesses(t *testing.T) {
	f := &fakeEC2{
		Pages:     [][]types.Snapshot{{snap("snap-1", 90, nil, ""), snap("snap-2", 80, nil, ""), snap("snap-3", 70, nil, "")}},
		DeleteErr: map[string]error{"snap-1": apiErr("InvalidSnapshot.InUse")},
	}
	cfg := baseConfig()
	cfg.MaxDeletes = 1
	res, err := Run(context.Background(), f, cfg)
	if err != nil {
		t.Fatal(err)
	}
	if !slices.Equal(res.Deleted, []string{"snap-2"}) {
		t.Fatalf("an in-use skip must not consume the cap; Deleted = %v", res.Deleted)
	}
}

func TestHiddenDescribeErrorIsWrappedAndNothingDeleted(t *testing.T) {
	boom := &smithy.GenericAPIError{Code: "AuthFailure", Message: "token expired"}
	f := &fakeEC2{DescribeErr: boom}
	_, err := Run(context.Background(), f, baseConfig())
	if err == nil || !errors.Is(err, boom) {
		t.Fatalf("describe error must be returned wrapped with %%w; got %v", err)
	}
	if errors.Is(err, ErrPartialFailure) {
		t.Fatal("a describe failure is not a partial delete failure")
	}
	if len(f.Deletes) != 0 {
		t.Fatal("deleted something after describe failed")
	}
}

func TestHiddenContextCancelStopsDeleting(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	f := &fakeEC2{
		Pages:    [][]types.Snapshot{{snap("snap-1", 90, nil, ""), snap("snap-2", 80, nil, ""), snap("snap-3", 70, nil, "")}},
		OnDelete: func(id string) { cancel() }, // SIGTERM arrives during the first delete
	}
	_, err := Run(ctx, f, baseConfig())
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("want an error wrapping context.Canceled, got %v", err)
	}
	if len(f.Deletes) != 1 {
		t.Fatalf("DeleteSnapshot called %d times after cancellation, want 1", len(f.Deletes))
	}
}

func TestHiddenRequiresOwnerID(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{snap("snap-1", 90, nil, "")}}}
	cfg := baseConfig()
	cfg.OwnerID = ""
	if _, err := Run(context.Background(), f, cfg); err == nil {
		t.Fatal("empty OwnerID must be rejected: DescribeSnapshots without OwnerIds lists public snapshots")
	}
	if len(f.Deletes) != 0 || len(f.DescribeInputs) != 0 {
		t.Fatal("no AWS calls expected with an invalid config")
	}
}

func TestHiddenNilTimesAndTagsDoNotPanic(t *testing.T) {
	f := &fakeEC2{Pages: [][]types.Snapshot{{
		{SnapshotId: aws.String("snap-weird"), Tags: []types.Tag{{Key: nil, Value: nil}}},
	}}}
	if _, err := Run(context.Background(), f, baseConfig()); err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

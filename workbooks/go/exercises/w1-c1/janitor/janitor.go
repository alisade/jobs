// Package janitor deletes expired EBS snapshots. It is the Go port of
// legacy/snapshot_janitor.py. See README.md for the full requirements.
package janitor

import (
	"context"
	"errors"
	"time"

	"github.com/aws/aws-sdk-go-v2/service/ec2"
)

// EC2API is the subset of the EC2 client the janitor uses. *ec2.Client
// satisfies it; tests use a fake. Keep it this small.
type EC2API interface {
	DescribeSnapshots(ctx context.Context, in *ec2.DescribeSnapshotsInput, optFns ...func(*ec2.Options)) (*ec2.DescribeSnapshotsOutput, error)
	DeleteSnapshot(ctx context.Context, in *ec2.DeleteSnapshotInput, optFns ...func(*ec2.Options)) (*ec2.DeleteSnapshotOutput, error)
}

// ErrPartialFailure is returned (wrapped, together with every underlying
// delete error) when at least one deletion failed for a reason that is not
// "in use" and not "dry run".
var ErrPartialFailure = errors.New("janitor: one or more deletions failed")

// Skip reasons recorded in Result.Skipped.
const (
	ReasonRetained   = "retained"    // keep tag set to true (case-insensitive)
	ReasonAMI        = "ami"         // description starts with "Created by CreateImage("
	ReasonInUse      = "in-use"      // DeleteSnapshot returned InvalidSnapshot.InUse
	ReasonMaxDeletes = "max-deletes" // safety cap reached
)

// Config mirrors the Python script's flags.
type Config struct {
	OwnerID       string
	RetentionDays int
	KeepTag       string // default "retain" when empty
	MaxDeletes    int    // 0 means no cap
	DryRun        bool
	// Now is injected for tests; nil means time.Now.
	Now func() time.Time
}

// Result reports what happened to every snapshot the janitor looked at, except
// snapshots that are simply younger than the retention window (those are ignored).
type Result struct {
	Deleted []string          // in deletion order (oldest first); in dry-run, the ones that would be deleted
	Skipped map[string]string // snapshot id -> Reason*
	Failed  map[string]error  // snapshot id -> error from DeleteSnapshot
}

// Run lists, filters and deletes snapshots. See README.md "Requirements".
func Run(ctx context.Context, api EC2API, cfg Config) (Result, error) {
	// TODO: implement. Suggested shape:
	//   1. page through DescribeSnapshots (ec2.NewDescribeSnapshotsPaginator)
	//   2. classify each snapshot (retained / ami / too young / candidate)
	//   3. sort candidates oldest first
	//   4. delete, mapping AWS error codes with errors.As + smithy.APIError
	//   5. aggregate failures with errors.Join and ErrPartialFailure
	_ = ctx
	_ = api
	_ = cfg
	return Result{}, errors.New("not implemented")
}

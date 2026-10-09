// Package janitor deletes expired EBS snapshots. It is the Go port of
// legacy/snapshot_janitor.py. See README.md for the full requirements.
package janitor

import (
	"cmp"
	"context"
	"errors"
	"fmt"
	"slices"
	"strings"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
	"github.com/aws/aws-sdk-go-v2/service/ec2/types"
	"github.com/aws/smithy-go"
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
	ReasonRetained   = "retained"
	ReasonAMI        = "ami"
	ReasonInUse      = "in-use"
	ReasonMaxDeletes = "max-deletes"
)

// Config mirrors the Python script's flags.
type Config struct {
	OwnerID       string
	RetentionDays int
	KeepTag       string
	MaxDeletes    int
	DryRun        bool
	Now           func() time.Time
}

// Result reports what happened to every snapshot the janitor looked at.
type Result struct {
	Deleted []string
	Skipped map[string]string
	Failed  map[string]error
}

const (
	codeDryRun = "DryRunOperation"
	codeInUse  = "InvalidSnapshot.InUse"
	amiPrefix  = "Created by CreateImage("
)

// Run lists, filters and deletes snapshots.
func Run(ctx context.Context, api EC2API, cfg Config) (Result, error) {
	if cfg.OwnerID == "" {
		return Result{}, errors.New("janitor: OwnerID is required")
	}
	keepTag := cmp.Or(cfg.KeepTag, "retain")
	now := time.Now
	if cfg.Now != nil {
		now = cfg.Now
	}
	cutoff := now().Add(-time.Duration(cfg.RetentionDays) * 24 * time.Hour)

	res := Result{Skipped: map[string]string{}, Failed: map[string]error{}}
	var candidates []types.Snapshot

	pager := ec2.NewDescribeSnapshotsPaginator(api, &ec2.DescribeSnapshotsInput{
		OwnerIds: []string{cfg.OwnerID},
	})
	for pager.HasMorePages() {
		page, err := pager.NextPage(ctx)
		if err != nil {
			return res, fmt.Errorf("janitor: describe snapshots: %w", err)
		}
		for _, s := range page.Snapshots {
			id := aws.ToString(s.SnapshotId)
			switch {
			case retained(s, keepTag):
				res.Skipped[id] = ReasonRetained
			case strings.HasPrefix(aws.ToString(s.Description), amiPrefix):
				res.Skipped[id] = ReasonAMI
			case !aws.ToTime(s.StartTime).Before(cutoff):
				// too young: ignored
			default:
				candidates = append(candidates, s)
			}
		}
	}

	slices.SortStableFunc(candidates, func(a, b types.Snapshot) int {
		return aws.ToTime(a.StartTime).Compare(aws.ToTime(b.StartTime))
	})

	var errs []error
	for _, s := range candidates {
		id := aws.ToString(s.SnapshotId)
		if err := ctx.Err(); err != nil {
			return res, fmt.Errorf("janitor: stopped before %s: %w", id, err)
		}
		if cfg.MaxDeletes > 0 && len(res.Deleted) >= cfg.MaxDeletes {
			res.Skipped[id] = ReasonMaxDeletes
			continue
		}
		_, err := api.DeleteSnapshot(ctx, &ec2.DeleteSnapshotInput{
			SnapshotId: aws.String(id),
			DryRun:     aws.Bool(cfg.DryRun),
		})
		switch code := apiCode(err); {
		case err == nil, code == codeDryRun:
			res.Deleted = append(res.Deleted, id)
		case code == codeInUse:
			res.Skipped[id] = ReasonInUse
		case errors.Is(err, context.Canceled), errors.Is(err, context.DeadlineExceeded):
			return res, fmt.Errorf("janitor: delete %s: %w", id, err)
		default:
			res.Failed[id] = err
			errs = append(errs, fmt.Errorf("delete %s: %w", id, err))
		}
	}
	if len(errs) > 0 {
		return res, errors.Join(append([]error{ErrPartialFailure}, errs...)...)
	}
	return res, nil
}

func retained(s types.Snapshot, keepTag string) bool {
	for _, t := range s.Tags {
		if aws.ToString(t.Key) == keepTag && strings.EqualFold(aws.ToString(t.Value), "true") {
			return true
		}
	}
	return false
}

func apiCode(err error) string {
	var ae smithy.APIError
	if errors.As(err, &ae) {
		return ae.ErrorCode()
	}
	return ""
}

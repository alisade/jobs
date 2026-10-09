package janitor

import (
	"context"
	"sync"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/service/ec2"
	"github.com/aws/aws-sdk-go-v2/service/ec2/types"
)

// fakeEC2 is an in-memory EC2API. Pages holds DescribeSnapshots pages in order;
// DeleteErr maps snapshot id -> error to return from DeleteSnapshot.
type fakeEC2 struct {
	mu          sync.Mutex
	Pages       [][]types.Snapshot
	DescribeErr error
	DeleteErr   map[string]error
	// recorded calls
	DescribeInputs []*ec2.DescribeSnapshotsInput
	Deletes        []string
	DeleteDryRun   []bool
	// OnDelete runs before each DeleteSnapshot returns (used to cancel ctx).
	OnDelete func(id string)
}

func (f *fakeEC2) DescribeSnapshots(ctx context.Context, in *ec2.DescribeSnapshotsInput, _ ...func(*ec2.Options)) (*ec2.DescribeSnapshotsOutput, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	f.DescribeInputs = append(f.DescribeInputs, in)
	if f.DescribeErr != nil {
		return nil, f.DescribeErr
	}
	idx := 0
	if in.NextToken != nil {
		for i := range f.Pages {
			if *in.NextToken == pageToken(i) {
				idx = i
			}
		}
	}
	out := &ec2.DescribeSnapshotsOutput{}
	if len(f.Pages) > 0 {
		out.Snapshots = f.Pages[idx]
	}
	if idx+1 < len(f.Pages) {
		out.NextToken = aws.String(pageToken(idx + 1))
	}
	return out, nil
}

func (f *fakeEC2) DeleteSnapshot(ctx context.Context, in *ec2.DeleteSnapshotInput, _ ...func(*ec2.Options)) (*ec2.DeleteSnapshotOutput, error) {
	id := aws.ToString(in.SnapshotId)
	f.mu.Lock()
	f.Deletes = append(f.Deletes, id)
	f.DeleteDryRun = append(f.DeleteDryRun, aws.ToBool(in.DryRun))
	hook := f.OnDelete
	err := f.DeleteErr[id]
	f.mu.Unlock()
	if hook != nil {
		hook(id)
	}
	if err != nil {
		return nil, err
	}
	return &ec2.DeleteSnapshotOutput{}, nil
}

func pageToken(i int) string { return "page-" + string(rune('a'+i)) }

var testNow = time.Date(2026, 3, 1, 2, 0, 0, 0, time.UTC)

func snap(id string, ageDays int, tags map[string]string, desc string) types.Snapshot {
	s := types.Snapshot{
		SnapshotId:  aws.String(id),
		StartTime:   aws.Time(testNow.Add(-time.Duration(ageDays) * 24 * time.Hour)),
		Description: aws.String(desc),
	}
	for k, v := range tags {
		s.Tags = append(s.Tags, types.Tag{Key: aws.String(k), Value: aws.String(v)})
	}
	return s
}

func baseConfig() Config {
	return Config{OwnerID: "111122223333", RetentionDays: 30, Now: func() time.Time { return testNow }}
}

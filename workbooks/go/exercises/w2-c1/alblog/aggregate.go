package alblog

import (
	"context"
	"errors"
	"io"
)

// Aggregate reads ALB log lines from r, parses them with `workers` goroutines
// (GOMAXPROCS when workers <= 0) and returns per-target-group stats. Malformed
// lines are counted, not fatal. A read error or context cancellation aborts the
// run and is returned wrapped. The result does not depend on `workers`.
//
// TODO: implement. Requirements are in README.md ("Aggregator").
func Aggregate(ctx context.Context, r io.Reader, workers int) (Report, error) {
	_, _, _ = ctx, r, workers
	return Report{}, errors.New("not implemented")
}

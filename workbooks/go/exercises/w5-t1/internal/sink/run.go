package sink

import (
	"context"
	"errors"
	"fmt"
	"log/slog"

	"github.com/twmb/franz-go/pkg/kerr"
	"github.com/twmb/franz-go/pkg/kgo"
)

// ErrFenced means the broker fenced this static member. The process exits and
// the kubelet restarts it, because a fenced client cannot rejoin by itself.
var ErrFenced = errors.New("sink: fenced by group coordinator")

// Run polls until ctx is done, hands every record to h, and commits after each
// successful batch. It returns ErrFenced (wrapped) when the broker fences us.
func Run(ctx context.Context, cl *kgo.Client, log *slog.Logger, h func(*kgo.Record) error) error {
	for {
		fs := cl.PollFetches(ctx)
		if ctx.Err() != nil {
			return nil
		}
		var fatal error
		fs.EachError(func(topic string, p int32, err error) {
			if errors.Is(err, kerr.FencedInstanceID) {
				fatal = fmt.Errorf("%w: %v", ErrFenced, err)
				return
			}
			log.Warn("fetch error", "topic", topic, "partition", p, "err", err)
		})
		if fatal != nil {
			return fatal
		}
		var herr error
		fs.EachRecord(func(r *kgo.Record) {
			if herr == nil {
				herr = h(r)
			}
		})
		if herr != nil {
			return fmt.Errorf("sink: handler: %w", herr)
		}
		if err := cl.CommitUncommittedOffsets(ctx); err != nil && ctx.Err() == nil {
			log.Warn("commit failed", "err", err)
		}
	}
}

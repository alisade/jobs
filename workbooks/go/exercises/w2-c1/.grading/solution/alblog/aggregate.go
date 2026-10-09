package alblog

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"io"
	"math"
	"runtime"
	"slices"
	"strings"
	"time"

	"golang.org/x/sync/errgroup"
)

const (
	batchSize   = 256
	maxLineSize = 1 << 20 // ALB lines with long URLs exceed bufio's 64 KiB default
)

type batch struct {
	first int // line number of lines[0]
	lines []string
}

type groupAcc struct {
	requests, elb5xx, target5xx int
	latencies                   []float64
}

type partial struct {
	lines, malformed int
	errs             []*ParseError
	groups           map[string]*groupAcc
}

// Aggregate reads ALB log lines from r, parses them with `workers` goroutines
// (GOMAXPROCS when workers <= 0) and returns per-target-group stats. Malformed
// lines are counted, not fatal. A read error or context cancellation aborts the
// run and is returned wrapped. The result does not depend on `workers`.
func Aggregate(ctx context.Context, r io.Reader, workers int) (Report, error) {
	if workers <= 0 {
		workers = runtime.GOMAXPROCS(0)
	}
	g, ctx := errgroup.WithContext(ctx)
	jobs := make(chan batch, workers)
	parts := make([]*partial, workers)

	// Producer: the only goroutine that touches r.
	g.Go(func() error {
		defer close(jobs)
		sc := bufio.NewScanner(r)
		sc.Buffer(make([]byte, 0, 64*1024), maxLineSize)
		lineNo := 0
		cur := batch{first: 1}
		send := func() error {
			if len(cur.lines) == 0 {
				return nil
			}
			select {
			case jobs <- cur:
			case <-ctx.Done():
				return ctx.Err()
			}
			cur = batch{first: lineNo + 1}
			return nil
		}
		for sc.Scan() {
			lineNo++
			if len(cur.lines) == 0 {
				cur.first = lineNo
			}
			cur.lines = append(cur.lines, sc.Text())
			if len(cur.lines) == batchSize {
				if err := send(); err != nil {
					return err
				}
			}
		}
		if err := sc.Err(); err != nil {
			return fmt.Errorf("read line %d: %w", lineNo+1, err)
		}
		return send()
	})

	for w := range workers {
		p := &partial{groups: map[string]*groupAcc{}}
		parts[w] = p
		g.Go(func() error {
			for b := range jobs {
				if err := ctx.Err(); err != nil {
					return err
				}
				for i, line := range b.lines {
					if strings.TrimSpace(line) == "" {
						continue
					}
					p.add(b.first+i, line)
				}
			}
			return ctx.Err()
		})
	}

	if err := g.Wait(); err != nil {
		return Report{}, fmt.Errorf("aggregate: %w", err)
	}
	return merge(parts), nil
}

func (p *partial) add(lineNo int, line string) {
	p.lines++
	e, err := ParseLine(lineNo, line)
	if err != nil {
		p.malformed++
		var pe *ParseError
		if errors.As(err, &pe) {
			p.errs = append(p.errs, pe)
		}
		return
	}
	key := e.TargetGroupARN
	if key == "" {
		key = "-"
	}
	acc := p.groups[key]
	if acc == nil {
		acc = &groupAcc{}
		p.groups[key] = acc
	}
	acc.requests++
	if e.ELBStatus >= 500 && e.ELBStatus <= 599 {
		acc.elb5xx++
	}
	if e.TargetStatus >= 500 && e.TargetStatus <= 599 {
		acc.target5xx++
	}
	if e.TargetProcessing >= 0 {
		acc.latencies = append(acc.latencies, e.TargetProcessing)
	}
}

func merge(parts []*partial) Report {
	var rep Report
	all := map[string]*groupAcc{}
	var errs []*ParseError
	for _, p := range parts {
		rep.Lines += p.lines
		rep.Malformed += p.malformed
		errs = append(errs, p.errs...)
		for k, a := range p.groups {
			t := all[k]
			if t == nil {
				t = &groupAcc{}
				all[k] = t
			}
			t.requests += a.requests
			t.elb5xx += a.elb5xx
			t.target5xx += a.target5xx
			t.latencies = append(t.latencies, a.latencies...)
		}
	}
	slices.SortFunc(errs, func(a, b *ParseError) int { return a.Line - b.Line })
	for _, e := range errs[:min(len(errs), MaxErrors)] {
		rep.FirstErrors = append(rep.FirstErrors, e)
	}
	for k, a := range all {
		slices.Sort(a.latencies)
		rep.Groups = append(rep.Groups, GroupStats{
			TargetGroup: k,
			Requests:    a.requests,
			ELB5xx:      a.elb5xx,
			Target5xx:   a.target5xx,
			P50:         percentile(a.latencies, 50),
			P99:         percentile(a.latencies, 99),
		})
	}
	slices.SortFunc(rep.Groups, func(a, b GroupStats) int { return strings.Compare(a.TargetGroup, b.TargetGroup) })
	return rep
}

// percentile is the nearest-rank percentile of sorted seconds, as a Duration.
func percentile(sorted []float64, p int) time.Duration {
	if len(sorted) == 0 {
		return 0
	}
	rank := (p*len(sorted) + 99) / 100 // ceil(p/100 * n)
	if rank < 1 {
		rank = 1
	}
	return time.Duration(math.Round(sorted[rank-1] * float64(time.Second)))
}

package alblog

import (
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"reflect"
	"runtime"
	"strings"
	"testing"
	"testing/iotest"
	"time"
)

const (
	tgA = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/a/1"
	tgB = "arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/b/2"
)

func readSample(t *testing.T) string {
	b, err := os.ReadFile("../testdata/sample.log")
	if err != nil {
		t.Fatal(err)
	}
	return string(b)
}

func TestHiddenAggregateDeterministicAcrossWorkerCounts(t *testing.T) {
	data := readSample(t)
	want, err := Aggregate(context.Background(), strings.NewReader(data), 1)
	if err != nil {
		t.Fatal(err)
	}
	for _, w := range []int{0, 2, 3, 16, 64} {
		got, err := Aggregate(context.Background(), strings.NewReader(data), w)
		if err != nil {
			t.Fatal(err)
		}
		if !reflect.DeepEqual(got, want) {
			t.Fatalf("workers=%d gives a different report than workers=1", w)
		}
	}
	if want.Groups[0].TargetGroup > want.Groups[1].TargetGroup {
		t.Fatal("Groups must be sorted by TargetGroup")
	}
}

func TestHiddenAggregatePercentilesAndCounts(t *testing.T) {
	var b strings.Builder
	for i := 1; i <= 100; i++ { // latencies 1..100 ms, shuffled order
		ms := (i*37)%100 + 1
		status := "200"
		if ms > 97 {
			status = "503"
		}
		b.WriteString(hline(map[int]string{6: fmt.Sprintf("%.3f", float64(ms)/1000), 8: status, 9: status, 16: tgA}) + "\n")
	}
	b.WriteString(hline(map[int]string{4: "-", 6: "-1", 8: "502", 9: "-", 16: tgA}) + "\n")
	b.WriteString(hline(map[int]string{6: "0.200", 16: "-"}) + "\n")
	b.WriteString("\n   \n")
	b.WriteString(hline(map[int]string{6: "0.010", 8: "200", 9: "500", 16: tgB}) + "\n")

	rep, err := Aggregate(context.Background(), strings.NewReader(b.String()), 4)
	if err != nil {
		t.Fatal(err)
	}
	if rep.Lines != 103 || rep.Malformed != 0 {
		t.Fatalf("Lines=%d Malformed=%d, want 103/0 (blank and whitespace-only lines are skipped)", rep.Lines, rep.Malformed)
	}
	want := []GroupStats{
		{TargetGroup: "-", Requests: 1, P50: 200 * time.Millisecond, P99: 200 * time.Millisecond},
		{TargetGroup: tgA, Requests: 101, ELB5xx: 4, Target5xx: 3, P50: 50 * time.Millisecond, P99: 99 * time.Millisecond},
		{TargetGroup: tgB, Requests: 1, Target5xx: 1, P50: 10 * time.Millisecond, P99: 10 * time.Millisecond},
	}
	if !reflect.DeepEqual(rep.Groups, want) {
		t.Fatalf("Groups =\n%+v\nwant\n%+v\n(nearest-rank percentiles; -1 latencies excluded; no target group -> \"-\")", rep.Groups, want)
	}
}

func TestHiddenAggregateFirstErrorsLowestLineNumbers(t *testing.T) {
	var b strings.Builder
	for i := 1; i <= 3000; i++ {
		if i%100 == 0 {
			b.WriteString(hline(map[int]string{8: "oops"}) + "\n")
		} else {
			b.WriteString(hline(nil) + "\n")
		}
	}
	rep, err := Aggregate(context.Background(), strings.NewReader(b.String()), 8)
	if err != nil {
		t.Fatal(err)
	}
	if rep.Malformed != 30 || len(rep.FirstErrors) != MaxErrors {
		t.Fatalf("Malformed=%d len(FirstErrors)=%d, want 30 and %d", rep.Malformed, len(rep.FirstErrors), MaxErrors)
	}
	for i, e := range rep.FirstErrors {
		var pe *ParseError
		if !errors.As(e, &pe) {
			t.Fatalf("FirstErrors[%d] is %T, want *ParseError", i, e)
		}
		if pe.Line != (i+1)*100 || pe.Field != "elb_status_code" {
			t.Fatalf("FirstErrors[%d] = line %d field %q, want line %d elb_status_code", i, pe.Line, pe.Field, (i+1)*100)
		}
	}
}

func TestHiddenAggregateLongLine(t *testing.T) {
	long := hline(map[int]string{12: `"GET https://api.harborlane.example:443/v1/x?q=` + strings.Repeat("a", 200_000) + ` HTTP/2.0"`})
	rep, err := Aggregate(context.Background(), strings.NewReader(long+"\n"+hline(nil)+"\n"), 2)
	if err != nil {
		t.Fatalf("lines longer than 64 KiB must not fail the run: %v", err)
	}
	if rep.Lines != 2 || rep.Malformed != 0 {
		t.Fatalf("Lines=%d Malformed=%d", rep.Lines, rep.Malformed)
	}
}

func TestHiddenAggregateEmptyInput(t *testing.T) {
	rep, err := Aggregate(context.Background(), strings.NewReader(""), 4)
	if err != nil || rep.Lines != 0 || len(rep.Groups) != 0 {
		t.Fatalf("empty input: rep=%+v err=%v", rep, err)
	}
}

func TestHiddenAggregateReadErrorPropagates(t *testing.T) {
	boom := errors.New("s3 stream reset")
	r := io.MultiReader(strings.NewReader(hline(nil)+"\n"), iotest.ErrReader(boom))
	_, err := Aggregate(context.Background(), r, 4)
	if !errors.Is(err, boom) {
		t.Fatalf("err = %v, want it to wrap the reader error", err)
	}
}

type infiniteLog struct{ line []byte }

func (r *infiniteLog) Read(p []byte) (int, error) {
	n := 0
	for n+len(r.line) <= len(p) {
		n += copy(p[n:], r.line)
	}
	if n == 0 {
		n = copy(p, r.line)
	}
	return n, nil
}

func settledGoroutines() int {
	n := runtime.NumGoroutine()
	for range 50 {
		time.Sleep(20 * time.Millisecond)
		m := runtime.NumGoroutine()
		if m == n {
			return m
		}
		n = m
	}
	return n
}

func TestHiddenAggregateCancellationNoLeak(t *testing.T) {
	before := settledGoroutines()
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() {
		_, err := Aggregate(ctx, &infiniteLog{line: []byte(hline(nil) + "\n")}, 8)
		done <- err
	}()
	time.Sleep(100 * time.Millisecond)
	cancel()
	select {
	case err := <-done:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("err = %v, want context.Canceled", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("Aggregate did not return within 3s of cancellation")
	}
	if after := settledGoroutines(); after > before {
		buf := make([]byte, 1<<16)
		n := runtime.Stack(buf, true)
		t.Fatalf("goroutine leak: %d before, %d after\n%s", before, after, buf[:n])
	}
}

func TestHiddenAggregatePreCancelled(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := Aggregate(ctx, strings.NewReader(readSample(t)), 4)
	if !errors.Is(err, context.Canceled) {
		t.Fatalf("err = %v, want context.Canceled", err)
	}
}

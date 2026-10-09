package alblog

import (
	"context"
	"os"
	"testing"
)

func TestAggregateSample(t *testing.T) {
	f, err := os.Open("../testdata/sample.log")
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	rep, err := Aggregate(context.Background(), f, 4)
	if err != nil {
		t.Fatalf("Aggregate: %v", err)
	}
	if rep.Lines != 402 || rep.Malformed != 2 {
		t.Fatalf("Lines=%d Malformed=%d, want 402 and 2 (blank lines are not counted)", rep.Lines, rep.Malformed)
	}
	if len(rep.Groups) != 3 {
		t.Fatalf("got %d groups, want 3", len(rep.Groups))
	}
}

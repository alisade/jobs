package alblog

import (
	"reflect"
	"testing"
)

// FuzzParse: go test -run '^$' -fuzz FuzzParse -fuzztime 60s ./alblog
// Plain `go test` runs only the seeds. Add seeds for every bug fuzzing finds.
func FuzzParse(f *testing.F) {
	f.Add(goodLine)
	f.Add("")
	f.Add(`"unterminated`)
	f.Fuzz(func(t *testing.T, line string) {
		e, err := Parse(line) // must never panic
		if err != nil {
			return
		}
		again, err := Parse(e.Format())
		if err != nil {
			t.Fatalf("Format output does not parse: %v\nline:   %q\nformat: %q", err, line, e.Format())
		}
		if !reflect.DeepEqual(e, again) {
			t.Fatalf("round trip changed the entry\nfirst:  %+v\nsecond: %+v", e, again)
		}
	})
}

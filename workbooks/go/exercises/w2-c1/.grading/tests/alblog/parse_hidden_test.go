package alblog

import (
	"errors"
	"reflect"
	"strings"
	"testing"
	"time"
)

// line builds an 18-field line from overrides of goodLine's first 18 tokens.
func hline(over map[int]string) string {
	f := []string{
		"h2", "2026-10-06T09:00:00.123456Z", "app/hl-public-alb/50dc6c495c0c9188", "203.0.113.233:34279",
		"10.42.6.151:8080", "0.000", "0.051", "0.001", "200", "200", "1079", "5014",
		`"GET https://api.harborlane.example:443/v1/x HTTP/2.0"`, `"okhttp/4.12.0"`,
		"ECDHE-RSA-AES128-GCM-SHA256", "TLSv1.2",
		"arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/hl-tracking-api/6d0ecf831eec9f09",
		`"Root=1-6f03675a-3d9c172411e20b8f6b0d549b"`,
	}
	for i, v := range over {
		f[i] = v
	}
	return strings.Join(f, " ")
}

func TestHiddenDashValuesAndUnreachableTarget(t *testing.T) {
	e, err := ParseLine(1, hline(map[int]string{4: "-", 6: "-1", 8: "502", 9: "-", 13: `"-"`, 14: "-", 15: "-"}))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if e.Target != "" || e.TargetStatus != 0 || e.TargetProcessing != -1 || e.ELBStatus != 502 {
		t.Fatalf("dash handling wrong: %+v", e)
	}
	if e.UserAgent != "" || e.SSLCipher != "" || e.SSLProtocol != "" {
		t.Fatalf(`"-" must become "" in string fields: %+v`, e)
	}
}

func TestHiddenQuotedFieldsWithSpacesAndEscapes(t *testing.T) {
	e, err := ParseLine(1, hline(map[int]string{13: `"HL-Carrier-Bot/2.1 \"beta\" (+https://harborlane.example/bots) C:\\tmp"`}))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if want := `HL-Carrier-Bot/2.1 "beta" (+https://harborlane.example/bots) C:\tmp`; e.UserAgent != want {
		t.Fatalf("UserAgent = %q, want %q", e.UserAgent, want)
	}
	if e.Request != "GET https://api.harborlane.example:443/v1/x HTTP/2.0" {
		t.Fatalf("Request = %q", e.Request)
	}
}

func TestHiddenTrailingFieldsIgnoredAndCRLF(t *testing.T) {
	base := hline(nil)
	e1, err := ParseLine(1, base)
	if err != nil {
		t.Fatalf("exactly %d fields must parse: %v", MinFields, err)
	}
	e2, err := ParseLine(1, base+` "api.harborlane.example" "arn:aws:acm:us-east-1:1:certificate/x" 1 2026-10-06T09:00:00Z "forward" "-" "-" "10.42.6.151:8080" "200" "-" "-" TID_1 "some future field"`+"\r")
	if err != nil {
		t.Fatalf("extra trailing fields (and a CRLF ending) must be ignored: %v", err)
	}
	if !reflect.DeepEqual(e1, e2) {
		t.Fatalf("trailing fields changed the entry:\n%+v\n%+v", e1, e2)
	}
}

func TestHiddenTimeNormalisedToUTC(t *testing.T) {
	e, err := ParseLine(1, hline(map[int]string{1: "2026-10-06T11:00:00.5+02:00"}))
	if err != nil {
		t.Fatal(err)
	}
	if e.Time.Location() != time.UTC || !e.Time.Equal(time.Date(2026, 10, 6, 9, 0, 0, 5e8, time.UTC)) {
		t.Fatalf("Time = %v (%v), want 09:00:00.5 UTC", e.Time, e.Time.Location())
	}
}

func TestHiddenParseErrorsAreTyped(t *testing.T) {
	tests := []struct {
		name      string
		line      string
		field     string
		sentinel  error
	}{
		{"status not a number", hline(map[int]string{8: "abc"}), "elb_status_code", ErrInvalidValue},
		{"status out of range", hline(map[int]string{9: "700"}), "target_status_code", ErrInvalidValue},
		{"NaN latency", hline(map[int]string{6: "NaN"}), "target_processing_time", ErrInvalidValue},
		{"Inf latency", hline(map[int]string{5: "+Inf"}), "request_processing_time", ErrInvalidValue},
		{"negative latency other than -1", hline(map[int]string{7: "-0.5"}), "response_processing_time", ErrInvalidValue},
		{"negative bytes", hline(map[int]string{10: "-3"}), "received_bytes", ErrInvalidValue},
		{"dash bytes", hline(map[int]string{11: "-"}), "sent_bytes", ErrInvalidValue},
		{"bad time", hline(map[int]string{1: "06/Oct/2026:09:00:00"}), "time", ErrInvalidValue},
		{"unterminated quote", hline(nil)[:200], "", ErrUnterminatedQuote},
		{"text after closing quote", hline(map[int]string{12: `"GET / HTTP/1.1"x`}), "", ErrMalformedQuote},
		{"too few fields", "h2 2026-10-06T09:00:00Z", "", ErrTooFewFields},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			_, err := ParseLine(42, tc.line)
			var pe *ParseError
			if !errors.As(err, &pe) {
				t.Fatalf("err = %v (%T), want *ParseError", err, err)
			}
			if pe.Line != 42 || pe.Field != tc.field {
				t.Fatalf("ParseError{Line:%d Field:%q}, want Line 42 Field %q", pe.Line, pe.Field, tc.field)
			}
			if !errors.Is(err, tc.sentinel) {
				t.Fatalf("errors.Is(err, %v) = false; err = %v", tc.sentinel, err)
			}
		})
	}
}

func TestHiddenRoundTripSeeds(t *testing.T) {
	for i, line := range []string{
		goodLine,
		hline(map[int]string{4: "-", 6: "-1", 9: "-"}),
		hline(map[int]string{13: `"a \"quoted\" agent \\ with backslash"`}),
		hline(map[int]string{13: `""`, 17: `"-"`}),
		hline(map[int]string{0: `"h2"`, 14: `"weird cipher"`}),
		hline(map[int]string{1: "2026-10-06T11:00:00.000000001+02:00"}),
		hline(map[int]string{8: "0200", 10: "+5"}),
	} {
		e, err := Parse(line)
		if err != nil {
			t.Fatalf("seed %d must parse: %v", i, err)
		}
		out := e.Format()
		again, err := Parse(out)
		if err != nil {
			t.Fatalf("seed %d: Format output does not parse: %v\n%q", i, err, out)
		}
		if !reflect.DeepEqual(e, again) {
			t.Fatalf("seed %d: round trip changed the entry\n%+v\n%+v", i, e, again)
		}
	}
}

func FuzzHiddenParse(f *testing.F) {
	for _, s := range []string{
		goodLine, "", " ", `"`, `"\`, `"\"`, `"" "" ""`, strings.Repeat("- ", 40),
		hline(map[int]string{6: "-1e0"}), hline(map[int]string{6: "1e400"}),
		hline(map[int]string{13: `"tab	and\nnewline"`}), hline(map[int]string{0: `a"b`}),
		hline(map[int]string{2: ""}), hline(map[int]string{1: "2026-10-06T09:00:00,5Z"}),
	} {
		f.Add(s)
	}
	f.Fuzz(func(t *testing.T, line string) {
		e, err := Parse(line)
		if err != nil {
			var pe *ParseError
			if !errors.As(err, &pe) {
				t.Fatalf("non-ParseError %T: %v", err, err)
			}
			return
		}
		again, err := Parse(e.Format())
		if err != nil || !reflect.DeepEqual(e, again) {
			t.Fatalf("round trip failed for %q: err=%v\n%+v\n%+v", line, err, e, again)
		}
	})
}

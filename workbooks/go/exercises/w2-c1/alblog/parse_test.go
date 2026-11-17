package alblog

import (
	"errors"
	"testing"
	"time"
)

const goodLine = `h2 2026-10-06T09:00:00.123456Z app/hl-public-alb/50dc6c495c0c9188 203.0.113.233:34279 10.42.6.151:8080 0.000 0.051 0.001 200 200 1079 5014 "GET https://api.harborlane.example:443/v1/shipments/HL514002/events HTTP/2.0" "okhttp/4.12.0" ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 arn:aws:elasticloadbalancing:us-east-1:123456789012:targetgroup/hl-tracking-api/6d0ecf831eec9f09 "Root=1-6f03675a-3d9c172411e20b8f6b0d549b" "api.harborlane.example" "-" 1 2026-10-06T09:00:00.120000Z "forward" "-" "-" "10.42.6.151:8080" "200" "-" "-" TID_0f21`

// Visible table-driven tests. Add your own rows; the hidden suite has many more.
func TestParseLine(t *testing.T) {
	tests := []struct {
		name    string
		line    string
		check   func(t *testing.T, e Entry)
		wantErr error // sentinel expected via errors.Is, nil for success
	}{
		{
			name: "full h2 line",
			line: goodLine,
			check: func(t *testing.T, e Entry) {
				if e.Type != "h2" || e.ELBStatus != 200 || e.TargetStatus != 200 || e.SentBytes != 5014 {
					t.Errorf("basic fields wrong: %+v", e)
				}
				if !e.Time.Equal(time.Date(2026, 10, 6, 9, 0, 0, 123456000, time.UTC)) {
					t.Errorf("Time = %v", e.Time)
				}
				if e.TargetProcessing != 0.051 {
					t.Errorf("TargetProcessing = %v", e.TargetProcessing)
				}
				if e.UserAgent != "okhttp/4.12.0" || e.Request != "GET https://api.harborlane.example:443/v1/shipments/HL514002/events HTTP/2.0" {
					t.Errorf("quoted fields wrong: %q %q", e.UserAgent, e.Request)
				}
			},
		},
		{
			name:    "truncated line",
			line:    `h2 2026-10-06T09:00:00.123456Z app/hl-public-alb/50dc6c495c0c9188`,
			wantErr: ErrTooFewFields,
		},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			e, err := ParseLine(7, tc.line)
			if tc.wantErr != nil {
				if !errors.Is(err, tc.wantErr) {
					t.Fatalf("err = %v, want %v", err, tc.wantErr)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			tc.check(t, e)
		})
	}
}

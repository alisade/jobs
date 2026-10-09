// Package alblog parses AWS Application Load Balancer access logs and
// aggregates them per target group. See README.md for the requirements.
package alblog

import (
	"errors"
	"fmt"
	"time"
)

// MinFields is the number of leading fields every line must have (type .. trace_id).
// ALB appends new fields over time; anything after field 17 is ignored.
const MinFields = 18

// Field names, in log order, used in ParseError.Field.
var FieldNames = [MinFields]string{
	"type", "time", "elb", "client:port", "target:port",
	"request_processing_time", "target_processing_time", "response_processing_time",
	"elb_status_code", "target_status_code", "received_bytes", "sent_bytes",
	"request", "user_agent", "ssl_cipher", "ssl_protocol", "target_group_arn", "trace_id",
}

// Entry is one parsed log line. A "-" in any string field is stored as "".
// Processing times are in seconds; -1 means "not available" (e.g. the target
// never answered). A "-" status code is stored as 0.
type Entry struct {
	Type               string
	Time               time.Time // always UTC
	ELB                string
	Client             string
	Target             string
	RequestProcessing  float64
	TargetProcessing   float64
	ResponseProcessing float64
	ELBStatus          int
	TargetStatus       int
	ReceivedBytes      int64
	SentBytes          int64
	Request            string // raw, e.g. "GET https://api.example:443/v1/x HTTP/1.1"
	UserAgent          string
	SSLCipher          string
	SSLProtocol        string
	TargetGroupARN     string
	TraceID            string
}

// Sentinel causes wrapped by ParseError.
var (
	ErrTooFewFields      = errors.New("too few fields")
	ErrUnterminatedQuote = errors.New("unterminated quoted field")
	ErrMalformedQuote    = errors.New("quoted field not followed by a space")
	ErrInvalidValue      = errors.New("invalid value")
)

// ParseError reports where a line failed to parse. Line is the 1-based line
// number (0 when unknown). Field is one of FieldNames, or "" for tokenizer
// errors that are not tied to one field.
type ParseError struct {
	Line  int
	Field string
	Err   error
}

func (e *ParseError) Error() string {
	if e.Field == "" {
		return fmt.Sprintf("line %d: %v", e.Line, e.Err)
	}
	return fmt.Sprintf("line %d: field %s: %v", e.Line, e.Field, e.Err)
}

func (e *ParseError) Unwrap() error { return e.Err }

// GroupStats aggregates every entry of one target group.
type GroupStats struct {
	TargetGroup string        // the ARN, or "-" for entries without a target group
	Requests    int           // number of entries
	ELB5xx      int           // ELBStatus in 500..599
	Target5xx   int           // TargetStatus in 500..599
	P50         time.Duration // nearest-rank percentile of TargetProcessing, ignoring -1
	P99         time.Duration // same, 99th
}

// Report is the result of Aggregate.
type Report struct {
	Lines       int          // non-empty lines read
	Malformed   int          // lines that failed to parse
	FirstErrors []error      // the parse errors with the lowest line numbers, at most MaxErrors, ascending
	Groups      []GroupStats // sorted by TargetGroup
}

// MaxErrors bounds Report.FirstErrors.
const MaxErrors = 10

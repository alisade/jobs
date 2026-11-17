package alblog

import (
	"fmt"
	"math"
	"strconv"
	"strings"
	"time"
)

// quotedFields are the positions ALB always writes in double quotes.
var quotedFields = map[int]bool{12: true, 13: true, 17: true}

// ParseLine parses one ALB access log line. lineNo is copied into any ParseError.
func ParseLine(lineNo int, line string) (Entry, error) {
	toks, err := tokenize(line)
	if err != nil {
		return Entry{}, &ParseError{Line: lineNo, Err: err}
	}
	if len(toks) < MinFields {
		return Entry{}, &ParseError{Line: lineNo, Err: fmt.Errorf("%w: got %d, want at least %d", ErrTooFewFields, len(toks), MinFields)}
	}
	p := fieldParser{toks: toks, line: lineNo}
	e := Entry{
		Type:               p.str(0),
		ELB:                p.str(2),
		Client:             p.str(3),
		Target:             p.str(4),
		RequestProcessing:  p.seconds(5),
		TargetProcessing:   p.seconds(6),
		ResponseProcessing: p.seconds(7),
		ELBStatus:          p.status(8),
		TargetStatus:       p.status(9),
		ReceivedBytes:      p.bytes(10),
		SentBytes:          p.bytes(11),
		Request:            p.str(12),
		UserAgent:          p.str(13),
		SSLCipher:          p.str(14),
		SSLProtocol:        p.str(15),
		TargetGroupARN:     p.str(16),
		TraceID:            p.str(17),
	}
	e.Time = p.time(1)
	if p.err != nil {
		return Entry{}, p.err
	}
	return e, nil
}

// Parse is ParseLine without a line number.
func Parse(line string) (Entry, error) { return ParseLine(0, line) }

// tokenize splits on single spaces. A token that starts with a double quote
// runs to the next unescaped quote, which must be followed by a space or the
// end of the line. Inside quotes, \" and \\ are unescaped; other backslashes
// are kept as-is.
func tokenize(line string) ([]string, error) {
	line = strings.TrimSuffix(line, "\r")
	var toks []string
	i := 0
	for {
		if i < len(line) && line[i] == '"' {
			var b strings.Builder
			j := i + 1
			closed := false
			for j < len(line) {
				c := line[j]
				if c == '\\' && j+1 < len(line) && (line[j+1] == '"' || line[j+1] == '\\') {
					b.WriteByte(line[j+1])
					j += 2
					continue
				}
				if c == '"' {
					closed = true
					break
				}
				b.WriteByte(c)
				j++
			}
			if !closed {
				return nil, ErrUnterminatedQuote
			}
			toks = append(toks, b.String())
			j++ // past closing quote
			if j == len(line) {
				return toks, nil
			}
			if line[j] != ' ' {
				return nil, ErrMalformedQuote
			}
			i = j + 1
			continue
		}
		sp := strings.IndexByte(line[i:], ' ')
		if sp < 0 {
			toks = append(toks, line[i:])
			return toks, nil
		}
		toks = append(toks, line[i:i+sp])
		i += sp + 1
	}
}

type fieldParser struct {
	toks []string
	line int
	err  error
}

func (p *fieldParser) fail(i int, format string, args ...any) {
	if p.err == nil {
		p.err = &ParseError{Line: p.line, Field: FieldNames[i], Err: fmt.Errorf("%w: "+format, append([]any{ErrInvalidValue}, args...)...)}
	}
}

func (p *fieldParser) str(i int) string {
	if p.toks[i] == "-" {
		return ""
	}
	return p.toks[i]
}

func (p *fieldParser) time(i int) time.Time {
	t, err := time.Parse(time.RFC3339Nano, p.toks[i])
	if err != nil {
		p.fail(i, "%q is not RFC 3339", p.toks[i])
		return time.Time{}
	}
	t = t.UTC()
	if y := t.Year(); y < 0 || y > 9999 {
		// Found by fuzzing: "0000-01-01T00:00:00+01:00" is year -1 in UTC and
		// cannot be formatted back as RFC 3339.
		p.fail(i, "%q is out of range in UTC", p.toks[i])
		return time.Time{}
	}
	return t
}

func (p *fieldParser) seconds(i int) float64 {
	v, err := strconv.ParseFloat(p.toks[i], 64)
	if err != nil || math.IsNaN(v) || math.IsInf(v, 0) || (v < 0 && v != -1) {
		p.fail(i, "%q is not -1 or a non-negative number of seconds", p.toks[i])
		return 0
	}
	return v
}

func (p *fieldParser) status(i int) int {
	if p.toks[i] == "-" {
		return 0
	}
	v, err := strconv.Atoi(p.toks[i])
	if err != nil || v < 100 || v > 599 {
		p.fail(i, "%q is not an HTTP status", p.toks[i])
		return 0
	}
	return v
}

func (p *fieldParser) bytes(i int) int64 {
	v, err := strconv.ParseInt(p.toks[i], 10, 64)
	if err != nil || v < 0 {
		p.fail(i, "%q is not a byte count", p.toks[i])
		return 0
	}
	return v
}

// Format renders e as a log line that ParseLine maps back to an equal Entry.
func (e Entry) Format() string {
	vals := []string{
		e.Type,
		e.Time.UTC().Format(time.RFC3339Nano),
		e.ELB, e.Client, e.Target,
		fmtSeconds(e.RequestProcessing), fmtSeconds(e.TargetProcessing), fmtSeconds(e.ResponseProcessing),
		fmtStatus(e.ELBStatus), fmtStatus(e.TargetStatus),
		strconv.FormatInt(e.ReceivedBytes, 10), strconv.FormatInt(e.SentBytes, 10),
		e.Request, e.UserAgent, e.SSLCipher, e.SSLProtocol, e.TargetGroupARN, e.TraceID,
	}
	stringField := map[int]bool{0: true, 2: true, 3: true, 4: true, 12: true, 13: true, 14: true, 15: true, 16: true, 17: true}
	var b strings.Builder
	for i, v := range vals {
		if i > 0 {
			b.WriteByte(' ')
		}
		if stringField[i] && v == "" {
			v = "-"
		}
		if quotedFields[i] || needsQuote(v) {
			b.WriteString(quote(v))
		} else {
			b.WriteString(v)
		}
	}
	return b.String()
}

func needsQuote(v string) bool {
	return v == "" || strings.ContainsAny(v, " \"\\")
}

func quote(v string) string {
	r := strings.NewReplacer(`\`, `\\`, `"`, `\"`)
	return `"` + r.Replace(v) + `"`
}

func fmtSeconds(v float64) string { return strconv.FormatFloat(v, 'f', -1, 64) }

func fmtStatus(v int) string {
	if v == 0 {
		return "-"
	}
	return strconv.Itoa(v)
}

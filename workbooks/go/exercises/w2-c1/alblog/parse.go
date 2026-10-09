package alblog

import "errors"

// ParseLine parses one ALB access log line. lineNo is copied into any ParseError.
//
// TODO: implement. Requirements are in README.md ("Parser"). Every error you
// return must be a *ParseError that wraps one of the sentinel errors in types.go.
func ParseLine(lineNo int, line string) (Entry, error) {
	_ = line
	return Entry{}, &ParseError{Line: lineNo, Err: errors.New("not implemented")}
}

// Parse is ParseLine without a line number.
func Parse(line string) (Entry, error) { return ParseLine(0, line) }

// Format renders e as a log line that ParseLine maps back to an equal Entry.
//
// TODO: implement. FuzzParse relies on it for the round-trip property.
func (e Entry) Format() string {
	return ""
}

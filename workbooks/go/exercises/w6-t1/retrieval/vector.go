package retrieval

import (
	"strconv"
	"strings"
)

// Vector is an embedding. Voyage voyage-3 returns 1024 float32 values,
// L2-normalised.
type Vector []float32

// String renders the pgvector text format, e.g. "[0.1,0.2,0.3]", which
// Postgres casts to vector when bound to a vector-typed parameter.
func (v Vector) String() string {
	var b strings.Builder
	b.Grow(len(v)*10 + 2)
	b.WriteByte('[')
	for i, f := range v {
		if i > 0 {
			b.WriteByte(',')
		}
		b.WriteString(strconv.FormatFloat(float64(f), 'f', -1, 32))
	}
	b.WriteByte(']')
	return b.String()
}

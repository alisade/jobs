package retrieval

import (
	"context"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// fakePlanner is a tiny model of how Postgres + pgvector 0.8 plan the search
// query against kb_chunks at production size (~2.1M rows). It is NOT a SQL
// parser; it only knows what matters for this incident:
//
//   - which HNSW index exists, read from migrations/*.sql
//   - whether the query's ORDER BY ... LIMIT can be served by that index
//
// If the index can serve the query it returns rows fast ("Index Scan").
// Otherwise it behaves like production: a Seq Scan + top-N sort over every
// tenant row, which blows the 3s statement_timeout set on the kb_reader role.
type fakePlanner struct {
	t        *testing.T
	opclass  string // e.g. vector_cosine_ops
	rows     [][]any
	lastSQL  string
	lastArgs []any
	lastPlan string
}

var (
	reIndex   = regexp.MustCompile(`(?is)using\s+hnsw\s*\(\s*embedding\s+(vector_\w+_ops)\s*\)`)
	reOrderBy = regexp.MustCompile(`(?is)order\s+by\s+(.+?)\s+limit\s+(\S+)`)
)

func newFakePlanner(t *testing.T, rows [][]any) *fakePlanner {
	t.Helper()
	files, err := filepath.Glob(filepath.Join("..", "migrations", "*.sql"))
	if err != nil || len(files) == 0 {
		t.Fatalf("no migrations found: %v", err)
	}
	p := &fakePlanner{t: t, rows: rows}
	for _, f := range files {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		if m := reIndex.FindStringSubmatch(string(b)); m != nil {
			p.opclass = m[1]
		}
	}
	if p.opclass == "" {
		t.Fatal("no HNSW index found in migrations")
	}
	return p
}

// operatorFor maps an operator class to the distance operator it indexes.
// Source: pgvector README, "HNSW" section.
func operatorFor(opclass string) string {
	switch opclass {
	case "vector_l2_ops":
		return "<->"
	case "vector_ip_ops":
		return "<#>"
	case "vector_cosine_ops":
		return "<=>"
	case "vector_l1_ops":
		return "<+>"
	}
	return "?"
}

func (p *fakePlanner) Query(ctx context.Context, sql string, args ...any) (Rows, error) {
	p.lastSQL, p.lastArgs = sql, args
	if p.indexUsable(sql) {
		p.lastPlan = "Limit -> Index Scan using kb_chunks_embedding_hnsw on kb_chunks c"
		return &fakeRows{rows: p.rows}, nil
	}
	p.lastPlan = "Limit -> Sort (top-N heapsort) -> Seq Scan on kb_chunks c (rows=2113847)"
	return nil, errors.New("ERROR: canceling statement due to statement timeout (SQLSTATE 57014)")
}

// indexUsable reports whether ORDER BY <embedding> <op> <param> [ASC] LIMIT n
// matches the index operator. An ORDER BY on an output alias is resolved to
// its SELECT-list expression, as Postgres does.
func (p *fakePlanner) indexUsable(sql string) bool {
	m := reOrderBy.FindStringSubmatch(sql)
	if m == nil {
		return false
	}
	expr := strings.TrimSpace(m[1])
	if strings.HasSuffix(strings.ToUpper(expr), " DESC") {
		return false
	}
	expr = strings.TrimSpace(strings.TrimSuffix(strings.TrimSuffix(expr, " ASC"), " asc"))
	if regexp.MustCompile(`^\w+$`).MatchString(expr) { // alias
		alias := regexp.MustCompile(`(?is)select\s.*?,?\s*([^,]+?)\s+as\s+` + regexp.QuoteMeta(expr) + `\b`)
		am := alias.FindStringSubmatch(sql)
		if am == nil {
			return false
		}
		expr = strings.TrimSpace(am[1])
	}
	want := regexp.MustCompile(`^(\w+\.)?embedding\s*` + regexp.QuoteMeta(operatorFor(p.opclass)) + `\s*\$\d+$`)
	return want.MatchString(expr)
}

type fakeRows struct {
	rows   [][]any
	i      int
	closed bool
}

func (r *fakeRows) Next() bool { r.i++; return r.i <= len(r.rows) }
func (r *fakeRows) Err() error { return nil }
func (r *fakeRows) Close()     { r.closed = true }
func (r *fakeRows) Scan(dest ...any) error {
	row := r.rows[r.i-1]
	if len(dest) != len(row) {
		return fmt.Errorf("scan: %d dest for %d columns", len(dest), len(row))
	}
	for i, v := range row {
		switch d := dest[i].(type) {
		case *int64:
			*d = v.(int64)
		case *string:
			*d = v.(string)
		case *float64:
			*d = v.(float64)
		default:
			return fmt.Errorf("scan: unsupported dest %T", dest[i])
		}
	}
	return nil
}

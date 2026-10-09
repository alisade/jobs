package retrieval

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// hiddenQuerier records the SQL and args and returns canned rows.
type hiddenQuerier struct {
	sql   string
	args  []any
	rows  *hiddenRows
	err   error
	calls int
}

func (q *hiddenQuerier) Query(_ context.Context, sql string, args ...any) (Rows, error) {
	q.calls++
	q.sql, q.args = sql, args
	if q.err != nil {
		return nil, q.err
	}
	if q.rows == nil {
		q.rows = &hiddenRows{}
	}
	return q.rows, nil
}

type hiddenRows struct {
	data   [][]any
	i      int
	closed bool
	err    error
}

func (r *hiddenRows) Next() bool { r.i++; return r.i <= len(r.data) }
func (r *hiddenRows) Err() error { return r.err }
func (r *hiddenRows) Close()     { r.closed = true }
func (r *hiddenRows) Scan(dest ...any) error {
	row := r.data[r.i-1]
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
			return fmt.Errorf("unsupported dest %T", dest[i])
		}
	}
	return nil
}

func hiddenSQL(t *testing.T, f Filter) (string, []any) {
	t.Helper()
	q := &hiddenQuerier{}
	if _, err := (&Repo{DB: q}).Search(context.Background(), Vector{0.6, 0.8}, f, 10); err != nil {
		t.Fatalf("Search: %v", err)
	}
	return q.sql, q.args
}

var hiddenOpRe = regexp.MustCompile(`<=>|<->|<#>|<\+>`)

func hiddenMigrationOpclass(t *testing.T) string {
	t.Helper()
	files, _ := filepath.Glob(filepath.Join("..", "migrations", "*.sql"))
	re := regexp.MustCompile(`(?is)using\s+hnsw\s*\(\s*embedding\s+(vector_\w+_ops)\s*\)`)
	for _, f := range files {
		b, err := os.ReadFile(f)
		if err != nil {
			t.Fatal(err)
		}
		if m := re.FindStringSubmatch(string(b)); m != nil {
			return m[1]
		}
	}
	t.Fatal("no hnsw index in migrations")
	return ""
}

func TestHiddenOperatorMatchesIndexOpclass(t *testing.T) {
	sql, _ := hiddenSQL(t, Filter{TenantID: "acme"})
	want := map[string]string{"vector_cosine_ops": "<=>", "vector_l2_ops": "<->", "vector_ip_ops": "<#>", "vector_l1_ops": "<+>"}[hiddenMigrationOpclass(t)]
	ops := hiddenOpRe.FindAllString(sql, -1)
	if len(ops) == 0 {
		t.Fatalf("no distance operator in SQL:\n%s", sql)
	}
	for _, op := range ops {
		if op != want {
			t.Fatalf("SQL uses %s but the HNSW index opclass serves %s; planner falls back to Seq Scan:\n%s", op, want, sql)
		}
	}
}

func TestHiddenUsesCosineDistance(t *testing.T) {
	sql, _ := hiddenSQL(t, Filter{TenantID: "acme"})
	if !strings.Contains(sql, "<=>") || strings.Contains(sql, "<->") || strings.Contains(sql, "<#>") {
		t.Fatalf("MinSimilarity is documented as cosine similarity; rank and score with <=>:\n%s", sql)
	}
}

func TestHiddenMigrationNotRewritten(t *testing.T) {
	// Fix the query, not the index: a REINDEX of 2.1M rows on prod was not approved,
	// and l2/ip opclasses would change the similarity contract.
	if got := hiddenMigrationOpclass(t); got != "vector_cosine_ops" {
		t.Fatalf("index opclass changed to %s; the fix belongs in the query", got)
	}
	b, err := os.ReadFile(filepath.Join("..", "migrations", "003_hnsw_index.sql"))
	if err != nil {
		t.Fatal(err)
	}
	sum := sha256.Sum256(b)
	if hex.EncodeToString(sum[:]) != hiddenMigrationSHA {
		t.Fatalf("migrations/003_hnsw_index.sql was edited; applied migrations are immutable")
	}
}

func TestHiddenOrderByIsIndexable(t *testing.T) {
	sql, _ := hiddenSQL(t, Filter{TenantID: "acme"})
	m := regexp.MustCompile(`(?is)order\s+by\s+(.+?)\s+limit\s+(\S+)`).FindStringSubmatch(sql)
	if m == nil {
		t.Fatalf("want ORDER BY <distance> LIMIT $n:\n%s", sql)
	}
	expr := strings.TrimSpace(m[1])
	if !regexp.MustCompile(`^\$\d+$`).MatchString(m[2]) {
		t.Fatalf("LIMIT must be a bind parameter, got %q", m[2])
	}
	if regexp.MustCompile(`(?i)\bdesc$`).MatchString(expr) {
		t.Fatalf("ORDER BY ... DESC on a similarity cannot use the HNSW index: %q", expr)
	}
	expr = strings.TrimSpace(regexp.MustCompile(`(?i)\s+asc$`).ReplaceAllString(expr, ""))
	if regexp.MustCompile(`^\w+$`).MatchString(expr) {
		am := regexp.MustCompile(`(?is)([^,\s][^,]*?)\s+as\s+` + regexp.QuoteMeta(expr) + `\b`).FindStringSubmatch(sql)
		if am == nil {
			t.Fatalf("ORDER BY alias %q not found in SELECT list", expr)
		}
		expr = strings.TrimSpace(am[1])
	}
	if !regexp.MustCompile(`^(\w+\.)?embedding\s*<=>\s*\$1$`).MatchString(expr) {
		t.Fatalf("ORDER BY must be the bare distance expression `embedding <=> $1` ascending (not 1 - ..., not a function), got %q", expr)
	}
}

func TestHiddenSimilarityIsOneMinusCosineDistance(t *testing.T) {
	q := &hiddenQuerier{rows: &hiddenRows{data: [][]any{
		{int64(1), "doc-a", "a", 0.10},
		{int64(2), "doc-b", "b", 0.25},
		{int64(3), "doc-c", "c", 0.35},
	}}}
	hits, err := (&Repo{DB: q}).Search(context.Background(), Vector{1, 0}, Filter{TenantID: "acme", MinSimilarity: 0.72}, 10)
	if err != nil {
		t.Fatal(err)
	}
	if len(hits) != 2 {
		t.Fatalf("MinSimilarity 0.72 should keep distances 0.10 and 0.25 only, got %d hits", len(hits))
	}
	if math.Abs(hits[0].Similarity-0.90) > 1e-9 || math.Abs(hits[1].Similarity-0.75) > 1e-9 {
		t.Fatalf("similarities = %v, %v; want 0.90, 0.75", hits[0].Similarity, hits[1].Similarity)
	}
	if hits[0].ChunkID != 1 || hits[1].DocID != "doc-b" {
		t.Fatalf("row mapping broken: %+v", hits)
	}
	if !q.rows.closed {
		t.Fatal("rows not closed: leaks a pooled connection")
	}
}

func TestHiddenTenantFilterIsParameterised(t *testing.T) {
	evil := "acme' OR '1'='1"
	sql, args := hiddenSQL(t, Filter{TenantID: evil})
	if strings.Contains(sql, evil) || strings.Contains(sql, "acme") {
		t.Fatalf("tenant id interpolated into SQL:\n%s", sql)
	}
	if !regexp.MustCompile(`(?i)tenant_id\s*=\s*\$\d+`).MatchString(sql) {
		t.Fatalf("tenant filter missing; this is a multi-tenant table:\n%s", sql)
	}
	found := false
	for _, a := range args {
		if a == evil {
			found = true
		}
	}
	if !found {
		t.Fatalf("tenant id not passed as an argument: %v", args)
	}
}

func TestHiddenCollectionFilterOptional(t *testing.T) {
	sql, args := hiddenSQL(t, Filter{TenantID: "acme"})
	if strings.Contains(sql, "collection") {
		t.Fatalf("no collection filter expected when Collection is empty:\n%s", sql)
	}
	sql2, args2 := hiddenSQL(t, Filter{TenantID: "acme", Collection: "runbooks"})
	m := regexp.MustCompile(`(?i)collection\s*=\s*\$(\d+)`).FindStringSubmatch(sql2)
	if m == nil {
		t.Fatalf("collection filter missing:\n%s", sql2)
	}
	var idx int
	fmt.Sscanf(m[1], "%d", &idx)
	if idx < 1 || idx > len(args2) || args2[idx-1] != "runbooks" {
		t.Fatalf("collection placeholder $%s does not bind \"runbooks\": %v", m[1], args2)
	}
	if len(args2) != len(args)+1 {
		t.Fatalf("args = %v / %v", args, args2)
	}
}

func TestHiddenPlaceholdersMatchArgs(t *testing.T) {
	for _, f := range []Filter{{TenantID: "t"}, {TenantID: "t", Collection: "c"}} {
		sql, args := hiddenSQL(t, f)
		max := 0
		for _, m := range regexp.MustCompile(`\$(\d+)`).FindAllStringSubmatch(sql, -1) {
			var n int
			fmt.Sscanf(m[1], "%d", &n)
			if n > max {
				max = n
			}
		}
		if max != len(args) {
			t.Fatalf("highest placeholder $%d but %d args:\n%s\n%v", max, len(args), sql, args)
		}
		if args[0] != "[0.6,0.8]" {
			t.Fatalf("$1 must be the pgvector literal, got %v", args[0])
		}
	}
}

func TestHiddenKValidationPreserved(t *testing.T) {
	q := &hiddenQuerier{}
	r := &Repo{DB: q}
	for _, k := range []int{0, -1, MaxK + 1} {
		if _, err := r.Search(context.Background(), Vector{1}, Filter{TenantID: "acme"}, k); !errors.Is(err, ErrBadK) {
			t.Fatalf("k=%d: want ErrBadK, got %v", k, err)
		}
	}
	if _, err := r.Search(context.Background(), Vector{1}, Filter{}, 5); err == nil {
		t.Fatal("empty tenant must be rejected")
	}
	if q.calls != 0 {
		t.Fatal("invalid input must not reach the database")
	}
}

func TestHiddenQueryErrorWrapped(t *testing.T) {
	boom := errors.New("ERROR: canceling statement due to statement timeout (SQLSTATE 57014)")
	_, err := (&Repo{DB: &hiddenQuerier{err: boom}}).Search(context.Background(), Vector{1}, Filter{TenantID: "acme"}, 5)
	if !errors.Is(err, boom) {
		t.Fatalf("query error must be wrapped with %%w, got %v", err)
	}
}

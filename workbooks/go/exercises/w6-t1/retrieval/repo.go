// Package retrieval is the pgvector-backed search behind the search_kb MCP tool.
//
// The repository talks to Postgres through the small Querier interface so it can
// be tested without a database. In production cmd/kb-retriever wraps a
// *pgxpool.Pool in an adapter that satisfies Querier (not part of this exercise).
package retrieval

import (
	"context"
	"errors"
	"fmt"
	"strconv"
	"strings"
)

// Querier is the subset of a Postgres pool the repository needs.
type Querier interface {
	Query(ctx context.Context, sql string, args ...any) (Rows, error)
}

// Rows is the subset of pgx.Rows the repository needs.
type Rows interface {
	Next() bool
	Scan(dest ...any) error
	Err() error
	Close()
}

// MaxK is the largest top-k the tool accepts; the agent never needs more.
const MaxK = 50

// ErrBadK is returned when k is outside 1..MaxK.
var ErrBadK = errors.New("retrieval: k must be between 1 and 50")

// Filter scopes a search. TenantID is mandatory (multi-tenant table).
type Filter struct {
	TenantID   string
	Collection string // optional; empty means all collections of the tenant
	// MinSimilarity drops hits whose cosine similarity is below this value.
	// The search_kb tool contract (docs/mcp-tools.md) documents 0.0-1.0 and
	// agents send 0.72 by default.
	MinSimilarity float64
}

// Hit is one retrieved chunk.
type Hit struct {
	ChunkID    int64
	DocID      string
	Content    string
	Similarity float64 // cosine similarity, 1 = identical direction
}

// Repo runs vector searches against the kb_chunks table.
type Repo struct {
	DB Querier
}

// distanceExpr is the vector distance used for ranking (refactored into one
// place in #412 so the SELECT list and ORDER BY can never disagree).
const distanceExpr = "c.embedding <-> $1"

// buildSearchSQL returns the SQL and its positional args. Every value goes in
// as a parameter; nothing user-controlled is concatenated into the string.
func buildSearchSQL(query Vector, f Filter, k int) (string, []any) {
	var b strings.Builder
	args := []any{query.String(), f.TenantID, k}

	b.WriteString("SELECT c.id, c.doc_id, c.content, ")
	b.WriteString(distanceExpr)
	b.WriteString(" AS distance\nFROM kb_chunks c\nWHERE c.tenant_id = $2")
	if f.Collection != "" {
		args = append(args, f.Collection)
		b.WriteString(" AND c.collection = $" + strconv.Itoa(len(args)))
	}
	b.WriteString("\nORDER BY ")
	b.WriteString(distanceExpr)
	b.WriteString("\nLIMIT $3")
	return b.String(), args
}

// Search returns up to k chunks most similar to query, best first, dropping
// hits below f.MinSimilarity.
func (r *Repo) Search(ctx context.Context, query Vector, f Filter, k int) ([]Hit, error) {
	if k < 1 || k > MaxK {
		return nil, ErrBadK
	}
	if f.TenantID == "" {
		return nil, errors.New("retrieval: tenant id is required")
	}
	sql, args := buildSearchSQL(query, f, k)
	rows, err := r.DB.Query(ctx, sql, args...)
	if err != nil {
		return nil, fmt.Errorf("retrieval: search tenant %s: %w", f.TenantID, err)
	}
	defer rows.Close()

	hits := make([]Hit, 0, k)
	for rows.Next() {
		var (
			h        Hit
			distance float64
		)
		if err := rows.Scan(&h.ChunkID, &h.DocID, &h.Content, &distance); err != nil {
			return nil, fmt.Errorf("retrieval: scan: %w", err)
		}
		h.Similarity = 1 - distance
		if h.Similarity < f.MinSimilarity {
			continue
		}
		hits = append(hits, h)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("retrieval: rows: %w", err)
	}
	return hits, nil
}

package retrieval

import (
	"context"
	"testing"
)

// Visible tests. TestSearchMeetsLatencyBudget reproduces the production
// symptom against fakePlanner (see planner_test.go).

func TestSearchMeetsLatencyBudget(t *testing.T) {
	p := newFakePlanner(t, [][]any{
		{int64(11), "runbook-eks-upgrade", "Drain nodes with ...", 0.12},
		{int64(42), "runbook-karpenter", "Consolidation can ...", 0.21},
	})
	repo := &Repo{DB: p}
	hits, err := repo.Search(context.Background(), Vector{0.1, 0.2, 0.3}, Filter{TenantID: "acme"}, 5)
	t.Logf("SQL:\n%s", p.lastSQL)
	t.Logf("plan: %s", p.lastPlan)
	if err != nil {
		t.Fatalf("search_kb timed out like production: %v", err)
	}
	if len(hits) != 2 {
		t.Fatalf("got %d hits, want 2", len(hits))
	}
}

func TestVectorString(t *testing.T) {
	if got := (Vector{0.5, -1, 0.25}).String(); got != "[0.5,-1,0.25]" {
		t.Fatalf("Vector.String() = %q", got)
	}
}

package router

import (
	"fmt"
	"strings"
	"sync"
	"testing"
)

func TestHiddenFirstMatchWinsAndTenantScoping(t *testing.T) {
	r, err := New(Config{DefaultTarget: "def", Rules: []Rule{
		{Name: "a-only", Tenant: "a", Label: "ns", Pattern: "web-.*", Target: "t-a"},
		{Name: "global-web", Label: "ns", Pattern: "web-.*", Target: "t-global"},
		{Name: "global-web-2", Label: "ns", Pattern: "web-prod", Target: "t-never"},
	}})
	if err != nil {
		t.Fatal(err)
	}
	if d := r.Route("a", map[string]string{"ns": "web-prod"}); d.Rule != "a-only" {
		t.Fatalf("tenant a: rule = %q, want a-only", d.Rule)
	}
	if d := r.Route("b", map[string]string{"ns": "web-prod"}); d.Rule != "global-web" || d.Target != "t-global" {
		t.Fatalf("tenant b: got %+v, want global-web (first match wins)", d)
	}
}

func TestHiddenPatternsAreAnchored(t *testing.T) {
	r := loadTestRouter(t)
	cases := map[string]string{
		"payments-prod":       "payments-prod",
		"payments-live-eu1":   "payments-prod",
		"xpayments-prod":      "default",
		"payments-prod-":      "default",
		"payments-staging":    "payments-staging",
		"payments-qa12":       "payments-staging",
		"payments-production": "default",
	}
	for ns, want := range cases {
		if d := r.Route("payments", map[string]string{"namespace": ns}); d.Rule != want {
			t.Errorf("namespace %q: rule = %q, want %q", ns, d.Rule, want)
		}
	}
}

func TestHiddenLabelsMergedWithoutAliasing(t *testing.T) {
	r := loadTestRouter(t)
	in := map[string]string{"namespace": "ledger-prod", "pod": "ledger-0"}
	d := r.Route("ledger", in)
	if len(in) != 2 {
		t.Fatalf("input map mutated: %v", in)
	}
	if d.Labels["team"] != "ledger" || d.Labels["pod"] != "ledger-0" {
		t.Fatalf("labels = %v", d.Labels)
	}
	d.Labels["team"] = "tampered"
	d2 := r.Route("ledger", map[string]string{"namespace": "ledger-prod", "pod": "ledger-0"})
	if d2.Labels["team"] != "ledger" {
		t.Fatal("mutating a returned Decision changed a later result (cache aliasing)")
	}
}

func TestHiddenGlobalRulesAndDefault(t *testing.T) {
	r := loadTestRouter(t)
	if d := r.Route("fraud", map[string]string{"namespace": "karpenter"}); d.Target != "cortex-platform" {
		t.Fatalf("karpenter -> %+v", d)
	}
	if d := r.Route("fraud", map[string]string{"namespace": "x", "pod": "web-canary-ab12c"}); d.Target != "cortex-canary" {
		t.Fatalf("canary pod -> %+v", d)
	}
	if d := r.Route("fraud", map[string]string{"job": "batch-20260101"}); d.Target != "cortex-batch" || d.Labels["retention"] != "7d" {
		t.Fatalf("batch job -> %+v", d)
	}
	d := r.Route("fraud", map[string]string{})
	if d.Target != "cortex-shared-default" || d.Rule != "default" || d.Labels == nil {
		t.Fatalf("empty labels -> %+v (Labels must be a non-nil map)", d)
	}
}

func TestHiddenNewRejectsBadConfig(t *testing.T) {
	if _, err := New(Config{DefaultTarget: "d", Rules: []Rule{{Name: "bad", Label: "ns", Pattern: "web-(", Target: "t"}}}); err == nil {
		t.Fatal("invalid pattern must fail New, not a request")
	} else if !strings.Contains(err.Error(), "bad") {
		t.Fatalf("error should name the rule: %v", err)
	}
	if _, err := New(Config{Rules: nil}); err == nil {
		t.Fatal("missing default_target must fail")
	}
}

func TestHiddenConcurrentRoute(t *testing.T) {
	r := loadTestRouter(t)
	var wg sync.WaitGroup
	for g := 0; g < 16; g++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := 0; i < 300; i++ {
				d := r.Route("search", map[string]string{"namespace": "search-prod", "pod": fmt.Sprintf("p-%d", i%50)})
				if d.Target != "cortex-search-prod" {
					t.Errorf("got %+v", d)
					return
				}
			}
		}()
	}
	wg.Wait()
}

// The regression: per-request work that belongs at load time. A cache miss
// that falls through every rule must stay cheap. Starter: ~460 allocs/op;
// a fixed hot path is well under 40 on any machine.
func TestHiddenCacheMissAllocationBudget(t *testing.T) {
	r := loadTestRouter(t)
	i := 0
	allocs := testing.AllocsPerRun(300, func() {
		i++
		r.Route("payments", map[string]string{"namespace": "sandbox-1", "pod": fmt.Sprint(i), "job": "x"})
	})
	if allocs > 40 {
		t.Fatalf("Route on a cache miss: %.0f allocs/op, budget 40. Profile it: go test -run XXX -bench . -benchmem -memprofile mem.out ./router", allocs)
	}
}

func TestHiddenMatchingRuleAllocationBudget(t *testing.T) {
	r := loadTestRouter(t)
	i := 0
	allocs := testing.AllocsPerRun(300, func() {
		i++
		r.Route("reco", map[string]string{"namespace": "reco-staging", "pod": fmt.Sprint(i)})
	})
	if allocs > 40 {
		t.Fatalf("Route matching a late rule: %.0f allocs/op, budget 40", allocs)
	}
}

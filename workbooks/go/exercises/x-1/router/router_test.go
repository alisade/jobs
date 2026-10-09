package router

import (
	"testing"
)

func loadTestRouter(t *testing.T) *Router {
	t.Helper()
	cfg, err := LoadConfig("../config/rules.json")
	if err != nil {
		t.Fatal(err)
	}
	r, err := New(cfg)
	if err != nil {
		t.Fatal(err)
	}
	return r
}

func TestRouteTenantProdNamespace(t *testing.T) {
	r := loadTestRouter(t)
	d := r.Route("checkout", map[string]string{"namespace": "checkout-prod", "pod": "checkout-api-1"})
	if d.Target != "cortex-checkout-prod" || d.Rule != "checkout-prod" {
		t.Fatalf("got %+v", d)
	}
	if d.Labels["tier"] != "prod" || d.Labels["team"] != "checkout" || d.Labels["pod"] != "checkout-api-1" {
		t.Fatalf("labels = %v", d.Labels)
	}
}

func TestRouteDefault(t *testing.T) {
	r := loadTestRouter(t)
	d := r.Route("checkout", map[string]string{"namespace": "sandbox-7"})
	if d.Target != "cortex-shared-default" || d.Rule != "default" {
		t.Fatalf("got %+v", d)
	}
}

package server

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/meridian/labelgate/router"
)

func TestRouteAPI(t *testing.T) {
	cfg, err := router.LoadConfig("../config/rules.json")
	if err != nil {
		t.Fatal(err)
	}
	r, err := router.New(cfg)
	if err != nil {
		t.Fatal(err)
	}
	body := `{"tenant":"search","series":[{"labels":{"namespace":"search-live"}},{"labels":{"namespace":"kube-system"}}]}`
	rec := httptest.NewRecorder()
	Handler(r).ServeHTTP(rec, httptest.NewRequest(http.MethodPost, "/api/v1/route", strings.NewReader(body)))
	if rec.Code != http.StatusOK {
		t.Fatalf("status %d: %s", rec.Code, rec.Body.String())
	}
	var out RouteResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &out); err != nil {
		t.Fatal(err)
	}
	if len(out.Results) != 2 || out.Results[0].Target != "cortex-search-prod" || out.Results[1].Target != "cortex-platform" {
		t.Fatalf("results = %+v", out.Results)
	}
}

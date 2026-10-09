// Package server exposes the router over HTTP. The remote-write gateway calls
// POST /api/v1/route with a batch of series for one tenant.
package server

import (
	"encoding/json"
	"net/http"

	"github.com/meridian/labelgate/router"
)

// Series is one metric series identified by its label set.
type Series struct {
	Labels map[string]string `json:"labels"`
}

// RouteRequest is the request body.
type RouteRequest struct {
	Tenant string   `json:"tenant"`
	Series []Series `json:"series"`
}

// RouteResult is one decision in the response, in request order.
type RouteResult struct {
	Target string            `json:"target"`
	Rule   string            `json:"rule"`
	Labels map[string]string `json:"labels"`
}

// RouteResponse is the response body.
type RouteResponse struct {
	Results []RouteResult `json:"results"`
}

// Handler returns the HTTP handler for the routing API.
func Handler(r *router.Router) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("POST /api/v1/route", func(w http.ResponseWriter, req *http.Request) {
		var in RouteRequest
		if err := json.NewDecoder(http.MaxBytesReader(w, req.Body, 4<<20)).Decode(&in); err != nil {
			http.Error(w, "bad request: "+err.Error(), http.StatusBadRequest)
			return
		}
		if in.Tenant == "" {
			http.Error(w, "tenant is required", http.StatusBadRequest)
			return
		}
		out := RouteResponse{Results: make([]RouteResult, 0, len(in.Series))}
		for _, s := range in.Series {
			d := r.Route(in.Tenant, s.Labels)
			out.Results = append(out.Results, RouteResult{Target: d.Target, Rule: d.Rule, Labels: d.Labels})
		}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(out)
	})
	mux.HandleFunc("GET /healthz", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(http.StatusOK) })
	return mux
}

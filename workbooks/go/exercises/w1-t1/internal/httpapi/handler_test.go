package httpapi

import (
	"io"
	"log/slog"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/corvidpay/flagd/internal/flags"
)

func newServer(t *testing.T) *httptest.Server {
	t.Helper()
	h := &Handler{Svc: &flags.Service{Store: flags.NewMemStore()}, Log: slog.New(slog.NewTextHandler(io.Discard, nil))}
	srv := httptest.NewServer(h.Routes())
	t.Cleanup(srv.Close)
	return srv
}

func do(t *testing.T, method, url, body string) (int, string) {
	t.Helper()
	req, err := http.NewRequest(method, url, strings.NewReader(body))
	if err != nil {
		t.Fatal(err)
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	return resp.StatusCode, string(b)
}

// The pager symptom: a perfectly valid PUT returns 500.
func TestPutValidFlagReturns200(t *testing.T) {
	srv := newServer(t)
	code, body := do(t, http.MethodPut, srv.URL+"/v1/flags/checkout-v2",
		`{"owner":"payments@corvidpay.example","env":"prod","enabled":true,"rollout":10}`)
	if code != http.StatusOK {
		t.Fatalf("PUT valid flag: status %d, body %s; want 200", code, body)
	}
}

func TestGetMissingFlagReturns404(t *testing.T) {
	srv := newServer(t)
	if code, body := do(t, http.MethodGet, srv.URL+"/v1/flags/nope-flag", ""); code != http.StatusNotFound {
		t.Fatalf("status %d body %s, want 404", code, body)
	}
}

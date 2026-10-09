package httpapi

import (
	"encoding/json"
	"net/http"
	"testing"
)

func TestHiddenPutValidThenGet(t *testing.T) {
	srv := newServer(t)
	code, body := do(t, http.MethodPut, srv.URL+"/v1/flags/ledger-batch-size",
		`{"description":"batch size","owner":"ledger@corvidpay.example","env":"staging","enabled":false,"rollout":0}`)
	if code != http.StatusOK {
		t.Fatalf("PUT: %d %s", code, body)
	}
	code, body = do(t, http.MethodGet, srv.URL+"/v1/flags/ledger-batch-size", "")
	if code != http.StatusOK {
		t.Fatalf("GET: %d %s", code, body)
	}
	var f map[string]any
	if err := json.Unmarshal([]byte(body), &f); err != nil {
		t.Fatal(err)
	}
	if f["owner"] != "ledger@corvidpay.example" || f["env"] != "staging" {
		t.Fatalf("GET body = %s", body)
	}
}

func TestHiddenPutInvalidReturns422WithFields(t *testing.T) {
	srv := newServer(t)
	code, body := do(t, http.MethodPut, srv.URL+"/v1/flags/Promo_2026", `{"owner":"growth","env":"qa","rollout":120}`)
	if code != http.StatusUnprocessableEntity {
		t.Fatalf("status %d body %s; want 422", code, body)
	}
	var eb struct {
		Error  string            `json:"error"`
		Fields map[string]string `json:"fields"`
	}
	if err := json.Unmarshal([]byte(body), &eb); err != nil {
		t.Fatalf("body not JSON: %s", body)
	}
	for _, k := range []string{"key", "owner", "env", "rollout"} {
		if eb.Fields[k] == "" {
			t.Fatalf("fields = %v; missing %q", eb.Fields, k)
		}
	}
}

func TestHiddenListDeleteAndErrors(t *testing.T) {
	srv := newServer(t)
	for _, k := range []string{"bbb-flag", "aaa-flag"} {
		if code, body := do(t, http.MethodPut, srv.URL+"/v1/flags/"+k,
			`{"owner":"o@corvidpay.example","env":"dev","enabled":true,"rollout":50}`); code != http.StatusOK {
			t.Fatalf("PUT %s: %d %s", k, code, body)
		}
	}
	code, body := do(t, http.MethodGet, srv.URL+"/v1/flags", "")
	var list []map[string]any
	if code != http.StatusOK || json.Unmarshal([]byte(body), &list) != nil || len(list) != 2 || list[0]["key"] != "aaa-flag" {
		t.Fatalf("LIST: %d %s", code, body)
	}
	if code, _ := do(t, http.MethodDelete, srv.URL+"/v1/flags/aaa-flag", ""); code != http.StatusNoContent {
		t.Fatalf("DELETE: %d", code)
	}
	if code, _ := do(t, http.MethodDelete, srv.URL+"/v1/flags/aaa-flag", ""); code != http.StatusNotFound {
		t.Fatalf("second DELETE: %d, want 404", code)
	}
	if code, _ := do(t, http.MethodPut, srv.URL+"/v1/flags/bbb-flag", `{"key":"other-key","owner":"o@x.example","env":"dev"}`); code != http.StatusBadRequest {
		t.Fatalf("mismatched key: %d, want 400", code)
	}
	if code, _ := do(t, http.MethodPut, srv.URL+"/v1/flags/bbb-flag", `{not json`); code != http.StatusBadRequest {
		t.Fatalf("bad JSON: %d, want 400", code)
	}
}

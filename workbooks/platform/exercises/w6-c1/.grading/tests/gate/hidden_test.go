package gate

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeTmp(t *testing.T, name, body string) string {
	t.Helper()
	p := filepath.Join(t.TempDir(), name)
	if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	return p
}

func runGate(args ...string) (int, string, string) {
	var o, e bytes.Buffer
	c := Run(args, &o, &e)
	return c, o.String(), e.String()
}

func TestHiddenCreateBeforeDestroyIsReplace(t *testing.T) {
	a, err := Classify(ResourceChange{Address: "a.b", Change: Change{Actions: []string{"create", "delete"}}})
	if err != nil || a != ActReplace {
		t.Fatalf("[create delete] = %q %v, want replace", a, err)
	}
	if a, _ := Classify(ResourceChange{Change: Change{Actions: []string{"read"}}}); a != ActRead {
		t.Fatalf("[read] = %q", a)
	}
	if _, err := Classify(ResourceChange{Address: "a.b", Change: Change{Actions: []string{"update", "delete"}}}); err == nil {
		t.Fatalf("unknown action combination must be an error")
	}
	if _, err := Classify(ResourceChange{Address: "a.b"}); err == nil {
		t.Fatalf("empty actions must be an error")
	}
}

func TestHiddenSummaryCountsReplaceLikeTerraform(t *testing.T) {
	s := Summarize(mustLoad(t, "../testdata/app-change.plan.json"))
	want := Summary{Import: 0, Add: 2, Change: 2, Destroy: 2, Replace: 1}
	if s != want {
		t.Fatalf("Summarize(app-change) = %+v, want %+v", s, want)
	}
	s = Summarize(mustLoad(t, "../testdata/import-batch-07-replace.plan.json"))
	if s != (Summary{Import: 3, Add: 1, Change: 1, Destroy: 1, Replace: 1}) {
		t.Fatalf("Summarize(replace) = %+v", s)
	}
}

func TestHiddenDataSourcesIgnored(t *testing.T) {
	p := Plan{FormatVersion: "1.2", ResourceChanges: []ResourceChange{
		{Address: "data.google_project.p", Mode: "data", Type: "google_project", Change: Change{Actions: []string{"read"}}},
	}}
	if s := Summarize(p); s != (Summary{}) {
		t.Fatalf("data source counted: %+v", s)
	}
	if v := Evaluate(p, Policy{ImportsOnly: true}); len(v) != 0 {
		t.Fatalf("data source violated: %v", v)
	}
}

func TestHiddenProtectedReplaceAndDelete(t *testing.T) {
	plan := mustLoad(t, "../testdata/import-batch-07-replace.plan.json")
	pol, _ := LoadPolicy("../testdata/policy-default.json")
	v := Evaluate(plan, pol)
	if len(v) != 1 || v[0].Address != "google_compute_network.riq_core" || v[0].Rule != "protected_type" {
		t.Fatalf("want one protected_type violation on the network, got %+v", v)
	}
	if !strings.Contains(v[0].Message, "replace_because_cannot_update") {
		t.Errorf("message should carry the action_reason: %q", v[0].Message)
	}
	p := Plan{FormatVersion: "1.2", ResourceChanges: []ResourceChange{
		{Address: "google_sql_database_instance.x", Mode: "managed", Type: "google_sql_database_instance", Change: Change{Actions: []string{"delete"}}},
		{Address: "google_compute_firewall.y", Mode: "managed", Type: "google_compute_firewall", Change: Change{Actions: []string{"delete"}}},
	}}
	v = Evaluate(p, pol)
	if len(v) != 1 || v[0].Address != "google_sql_database_instance.x" {
		t.Fatalf("only the protected delete violates outside imports-only: %+v", v)
	}
}

func TestHiddenImportsOnlyRules(t *testing.T) {
	pol, _ := LoadPolicy("../testdata/policy-migration.json")
	v := Evaluate(mustLoad(t, "../testdata/import-batch-07.plan.json"), pol)
	if len(v) != 0 {
		t.Fatalf("labels-only update on import is allowed: %+v", v)
	}
	v = Evaluate(mustLoad(t, "../testdata/import-batch-07-replace.plan.json"), pol)
	rules := []string{}
	for _, x := range v {
		rules = append(rules, x.Address+"|"+x.Rule)
	}
	want := "google_compute_firewall.riq_allow_iap|imports_only_attribute,google_compute_network.riq_core|imports_only_action,google_compute_network.riq_core|protected_type"
	if strings.Join(rules, ",") != want {
		t.Fatalf("violations = %v\nwant %s (sorted by address, then rule)", rules, want)
	}
	v = Evaluate(mustLoad(t, "../testdata/app-change.plan.json"), pol)
	n := 0
	for _, x := range v {
		if x.Rule == "imports_only_action" {
			n++
		}
	}
	if n != 3 {
		t.Fatalf("create, delete and replace each violate imports-only; got %d: %+v", n, v)
	}
}

func TestHiddenChangedAttributesAndMasking(t *testing.T) {
	plan := mustLoad(t, "../testdata/app-change.plan.json")
	var sec ResourceChange
	for _, rc := range plan.ResourceChanges {
		if rc.Type == "google_secret_manager_secret_version" {
			sec = rc
		}
	}
	ch := ChangedAttributes(sec)
	if len(ch) != 1 || ch[0].Name != "secret_data" || ch[0].Before != Sensitive || ch[0].After != Sensitive {
		t.Fatalf("secret_data must be masked: %+v", ch)
	}
	nested := ResourceChange{Change: Change{Actions: []string{"update"},
		Before:          map[string]any{"settings": map[string]any{"pw": "a"}, "tier": "x"},
		After:           map[string]any{"settings": map[string]any{"pw": "b"}, "tier": "y"},
		BeforeSensitive: map[string]any{"settings": map[string]any{"pw": true}},
		AfterSensitive:  map[string]any{"settings": map[string]any{"pw": true}}}}
	ch = ChangedAttributes(nested)
	if len(ch) != 2 || ch[0].Name != "settings" || ch[0].After != Sensitive || ch[1].Name != "tier" || ch[1].After != `"y"` {
		t.Fatalf("nested sensitive marker must mask the whole attribute, others rendered as JSON: %+v", ch)
	}
	added := ResourceChange{Change: Change{Actions: []string{"update"}, Before: map[string]any{}, After: map[string]any{"labels": map[string]any{"team": "riq"}}}}
	ch = ChangedAttributes(added)
	if len(ch) != 1 || ch[0].Before != "null" || ch[0].After != `{"team":"riq"}` {
		t.Fatalf("added attribute: %+v", ch)
	}
}

func TestHiddenNoSecretInAnyOutput(t *testing.T) {
	for _, flags := range [][]string{{}, {"-json"}} {
		args := append([]string{"-plan", "../testdata/app-change.plan.json"}, flags...)
		_, out, _ := runGate(args...)
		if strings.Contains(out, "new-pass-2") || strings.Contains(out, "old-pass-1") {
			t.Fatalf("secret leaked with flags %v:\n%s", flags, out)
		}
		_, out, _ = runGate("-plan", "../testdata/import-batch-07.plan.json", "-json")
		if strings.Contains(out, "s3cr3t") {
			t.Fatalf("sql user password leaked")
		}
	}
}

func TestHiddenJSONReport(t *testing.T) {
	code, out, _ := runGate("-plan", "../testdata/import-batch-07-replace.plan.json", "-policy", "../testdata/policy-migration.json", "-json")
	if code != ExitViolation {
		t.Fatalf("exit %d", code)
	}
	var rep Report
	if err := json.Unmarshal([]byte(out), &rep); err != nil {
		t.Fatalf("stdout must be only the JSON report: %v\n%s", err, out)
	}
	if rep.Result != "fail" || rep.Summary.Replace != 1 || len(rep.Violations) != 3 {
		t.Fatalf("report = %+v", rep)
	}
	addrs := []string{}
	for _, c := range rep.Changes {
		addrs = append(addrs, c.Address)
	}
	if strings.Join(addrs, ",") != "google_compute_firewall.riq_allow_iap,google_compute_network.riq_core,google_compute_subnetwork.riq_gke_usc1" {
		t.Fatalf("changes must be sorted by address and include imports: %v", addrs)
	}
	for _, c := range rep.Changes {
		if c.Address == "google_compute_network.riq_core" {
			if c.Action != ActReplace || !c.Importing || len(c.ReplacePaths) != 1 || c.ReplacePaths[0] != "auto_create_subnetworks" {
				t.Fatalf("network entry = %+v", c)
			}
		}
	}
	_, out, _ = runGate("-plan", "../testdata/import-batch-07.plan.json", "-json")
	if !strings.Contains(out, `"violations": []`) {
		t.Fatalf("violations must be an empty array, not null:\n%s", out)
	}
}

func TestHiddenTextReport(t *testing.T) {
	code, out, _ := runGate("-plan", "../testdata/import-batch-07-replace.plan.json", "-policy", "../testdata/policy-migration.json")
	if code != ExitViolation {
		t.Fatalf("exit %d", code)
	}
	for _, s := range []string{"forces replacement: auto_create_subnetworks", "RESULT: FAIL", "(1 replacement(s))", "VIOLATION google_compute_network.riq_core"} {
		if !strings.Contains(out, s) {
			t.Errorf("text output missing %q:\n%s", s, out)
		}
	}
	code, _, _ = runGate("-plan", "../testdata/app-change.plan.json")
	if code != ExitPass {
		t.Fatalf("no policy means no violations; exit %d", code)
	}
}

func TestHiddenUsageAndParseErrors(t *testing.T) {
	cases := map[string][]string{
		"no -plan":        {},
		"missing file":    {"-plan", "/nonexistent/plan.json"},
		"bad json":        {"-plan", writeTmp(t, "bad.json", "{not json")},
		"not a plan":      {"-plan", writeTmp(t, "state.json", `{"version":4,"resources":[]}`)},
		"format 2.0":      {"-plan", writeTmp(t, "v2.json", `{"format_version":"2.0","resource_changes":[]}`)},
		"unknown action":  {"-plan", writeTmp(t, "u.json", `{"format_version":"1.2","resource_changes":[{"address":"a.b","mode":"managed","type":"a","change":{"actions":["update","delete"]}}]}`)},
		"bad policy json": {"-plan", "../testdata/app-change.plan.json", "-policy", writeTmp(t, "p.json", "[")},
	}
	for name, args := range cases {
		code, out, errOut := runGate(args...)
		if code != ExitUsage {
			t.Errorf("%s: exit %d, want 2", name, code)
		}
		if strings.TrimSpace(errOut) == "" {
			t.Errorf("%s: explain the error on stderr", name)
		}
		if strings.Contains(out, "RESULT: PASS") {
			t.Errorf("%s: must not report PASS", name)
		}
	}
}

func TestHiddenEmptyPlanPasses(t *testing.T) {
	code, out, _ := runGate("-plan", writeTmp(t, "e.json", `{"format_version":"1.2"}`), "-policy", "../testdata/policy-migration.json")
	if code != ExitPass || !strings.Contains(out, "Plan: 0 to import, 0 to add, 0 to change, 0 to destroy.") {
		t.Fatalf("empty plan: exit %d\n%s", code, out)
	}
}

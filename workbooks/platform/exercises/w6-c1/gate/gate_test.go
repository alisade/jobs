package gate

import (
	"bytes"
	"strings"
	"testing"
)

func mustLoad(t *testing.T, path string) Plan {
	t.Helper()
	p, err := LoadPlan(path)
	if err != nil {
		t.Fatal(err)
	}
	return p
}

func TestClassifyBasicActions(t *testing.T) {
	cases := map[string]Action{"no-op": ActNoOp, "create": ActCreate, "update": ActUpdate, "delete": ActDelete, "delete,create": ActReplace}
	for in, want := range cases {
		got, err := Classify(ResourceChange{Address: "x.y", Change: Change{Actions: strings.Split(in, ",")}})
		if err != nil || got != want {
			t.Errorf("Classify(%s) = %q, %v; want %q", in, got, err, want)
		}
	}
}

func TestSummarizeImportBatch(t *testing.T) {
	s := Summarize(mustLoad(t, "../testdata/import-batch-07.plan.json"))
	want := Summary{Import: 5, Add: 0, Change: 1, Destroy: 0, Replace: 0}
	if s != want {
		t.Fatalf("Summarize = %+v, want %+v", s, want)
	}
}

func TestRunCleanMigrationPlanPasses(t *testing.T) {
	var out, errb bytes.Buffer
	code := Run([]string{"-plan", "../testdata/import-batch-07.plan.json", "-policy", "../testdata/policy-migration.json"}, &out, &errb)
	if code != ExitPass {
		t.Fatalf("exit %d, want 0; stdout:\n%s\nstderr:\n%s", code, out.String(), errb.String())
	}
	if !strings.Contains(out.String(), "Plan: 5 to import, 0 to add, 1 to change, 0 to destroy.") {
		t.Fatalf("summary line missing:\n%s", out.String())
	}
}

func TestRunReplaceInMigrationFails(t *testing.T) {
	var out, errb bytes.Buffer
	code := Run([]string{"-plan", "../testdata/import-batch-07-replace.plan.json", "-policy", "../testdata/policy-migration.json"}, &out, &errb)
	if code != ExitViolation {
		t.Fatalf("exit %d, want 1 (the VPC would be replaced); stdout:\n%s", code, out.String())
	}
}

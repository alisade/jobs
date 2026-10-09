#!/usr/bin/env bash
# Hidden-test harness. Run from the exercise folder: bash .grading/grade.sh
# Copies the exercise to a temp dir, overlays .grading/tests/, runs go test -json,
# and prints GRADE_TESTS {"passed": P, "total": T} as the last line.
set -uo pipefail

ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
work="$(mktemp -d "${TMPDIR:-/tmp}/grade-XXXXXX")"
trap 'rm -rf "${work}"' EXIT

# ---- per-exercise settings -------------------------------------------------
GO_TEST_FLAGS="${GO_TEST_FLAGS:-}"        # no -race: envtest + controller-runtime under -race is slow
GO_TEST_TIMEOUT="${GO_TEST_TIMEOUT:-240s}"
PKGS="./..."
ENVTEST_K8S_VERSION="1.37.0"
# Runs inside the temp copy before go test: keep the learner's committed role.yaml
# for comparison, regenerate role.yaml from the markers, point envtest at its binaries.
pre_test() {
  cp config/rbac/role.yaml config/rbac/role.committed.yaml 2>/dev/null || true
  go tool controller-gen rbac:roleName=manager-role paths="./..." output:rbac:artifacts:config=config/rbac \
    || echo "grade.sh: controller-gen failed (does the code compile?)"
  KUBEBUILDER_ASSETS="$(go tool setup-envtest use "${ENVTEST_K8S_VERSION}" -p path)" \
    || die "setup-envtest could not provide kube-apiserver/etcd ${ENVTEST_K8S_VERSION}"
  export KUBEBUILDER_ASSETS
}
# -----------------------------------------------------------------------------

die() { echo "grade.sh: harness error: ${1}" >&2; echo 'GRADE_TESTS {"passed": 0, "total": 0}'; exit 2; }
command -v go >/dev/null 2>&1 || die "go not found on PATH (tools/doctor.sh go)"

# Copy learner files (everything except .grading and build output), then overlay hidden tests.
(cd "${ex_dir}" && tar --exclude ./.grading --exclude ./bin -cf - .) | (cd "${work}" && tar -xf -) \
  || die "could not copy exercise to ${work}"
cp -R "${ex_dir}/.grading/tests/." "${work}/" || die "could not overlay hidden tests"

cd "${work}" || die "cd ${work}"
pre_test

# Expected test count = every top-level Test/Fuzz func in *_test.go (visible + hidden),
# so a compile failure scores 0/N instead of 0/0.
total=$(grep -rhoE '^func (Test|Fuzz)[A-Za-z0-9_]*\((t|f) \*testing\.(T|F)\)' --include='*_test.go' . | grep -v '^func TestMain' | wc -l | tr -d ' ')

echo "== go vet"
go vet ./... 2>&1 | tail -20 || true

echo "== go test ${GO_TEST_FLAGS} (timeout ${GO_TEST_TIMEOUT})"
go test -json -count=1 ${GO_TEST_FLAGS} -timeout "${GO_TEST_TIMEOUT}" ${PKGS} > "${work}/test.json" 2> "${work}/test.stderr"
# Human-readable summary: failures with their output, then pass/fail per test.
grep -E '"Action":"output"' "${work}/test.json" | grep -E '"Output":"(--- FAIL|    |FAIL|panic|.*\.go:[0-9]+:)' \
  | sed -E 's/.*"Output":"(.*)"}$/\1/; s/\\n$//; s/\\t/  /g; s/\\"/"/g' | head -120
tail -20 "${work}/test.stderr"

passed=$(grep -E '"Action":"pass"' "${work}/test.json" | grep -cE '"Test":"[^"/]+"' || true)
failed=$(grep -E '"Action":"fail"' "${work}/test.json" | grep -cE '"Test":"[^"/]+"' || true)
echo "== top-level tests: passed=${passed} failed=${failed} expected=${total}"
grep -E '"Action":"(pass|fail|skip)"' "${work}/test.json" | grep -E '"Test":"[^"/]+"' \
  | sed -E 's/.*"Action":"([a-z]+)".*"Test":"([^"]+)".*/  \1  \2/' | sort -k2

if [ "${passed}" -gt "${total}" ]; then total="${passed}"; fi
echo "GRADE_TESTS {\"passed\": ${passed}, \"total\": ${total}}"
exit 0

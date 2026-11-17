#!/usr/bin/env bash
# Shared grader for Go exercises. Copies the exercise to a temp dir (the learner's folder is never
# written to), overlays .grading/tests/ onto it, runs go vet and go test -json with a timeout, and
# prints GRADE_TESTS {"passed": P, "total": T} as the last line.
# Usage: grade-go.sh <ex_dir> [timeout like 180s]
set -uo pipefail
ex_dir="${1:?ex_dir}"; go_timeout="${2:-180s}"
work="$(mktemp -d "${TMPDIR:-/tmp}/platform-grade-XXXXXX")"
trap 'rm -rf "${work}"' EXIT

die() { echo "HARNESS ERROR: ${1}" >&2; echo 'GRADE_TESTS {"passed": 0, "total": 0}'; exit 2; }
command -v go >/dev/null 2>&1 || die "go not found on PATH (tools/doctor.sh platform)"

(cd "${ex_dir}" && tar --exclude ./.grading --exclude ./bin -cf - .) | (cd "${work}" && tar -xf -) \
  || die "could not copy exercise to ${work}"
if [ -d "${ex_dir}/.grading/tests" ]; then
  cp -R "${ex_dir}/.grading/tests/." "${work}/" || die "could not overlay hidden tests"
fi
cd "${work}" || die "cd ${work}"
export GOFLAGS="${GOFLAGS:--mod=mod}" GOTOOLCHAIN=local GOPROXY=off

# Expected total = every top-level Test func in *_test.go (visible + hidden), so a compile
# failure scores 0/N instead of 0/0.
total=$(grep -rhoE '^func Test[A-Za-z0-9_]*\(t \*testing\.T\)' --include='*_test.go' . | wc -l | tr -d ' ')

echo "== go vet"
go vet ./... 2>&1 | tail -20 || true
echo "== go test -race (timeout ${go_timeout})"
go test -json -count=1 -race -timeout "${go_timeout}" ./... > "${work}/test.json" 2> "${work}/test.stderr"
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

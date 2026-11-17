#!/usr/bin/env bash
# Shared grader for Go exercises (stdlib only, no module downloads). Copies the exercise to a temp
# dir, overlays .grading/tests/ (same package layout as the exercise), runs go vet and
# go test -json -race, prints one line per top-level test, then:
#   GRADE_TESTS {"passed": P, "total": T}
# The expected total counts every top-level Test func in *_test.go (visible + hidden), so a
# compile failure scores 0/N instead of 0/0.
# Usage: grade-go.sh <ex_dir> [timeout like 180s]
set -uo pipefail
ex_dir="${1:?ex_dir}"; go_timeout="${2:-180s}"
die() { echo "grade-go.sh: harness error: ${1}" >&2; echo "HARNESS ERROR: ${1}"; exit 2; }
command -v go >/dev/null 2>&1 || die "go not found on PATH (tools/doctor.sh backend)"
work="$(mktemp -d "${TMPDIR:-/tmp}/grade-backend-go.XXXXXX")"
trap 'rm -rf "${work}"' EXIT
(cd "${ex_dir}" && tar --exclude ./.grading --exclude ./bin -cf - .) | (cd "${work}" && tar -xf -) \
  || die "could not copy exercise to ${work}"
if [ -d "${ex_dir}/.grading/tests" ]; then cp -R "${ex_dir}/.grading/tests/." "${work}/" || die "could not overlay hidden tests"; fi
cd "${work}" || die "cd ${work}"
export GOFLAGS="-mod=mod" GOTOOLCHAIN=local GOPROXY=off
total=$(grep -rhoE '^func Test[A-Za-z0-9_]*\(t \*testing\.T\)' --include='*_test.go' . | wc -l | tr -d ' ')
echo "== go vet"
go vet ./... 2>&1 | tail -20 || true
echo "== go test -race (timeout ${go_timeout})"
go test -json -count=1 -race -timeout "${go_timeout}" ./... > "${work}/test.json" 2> "${work}/test.stderr"
grep -E '"Action":"output"' "${work}/test.json" | grep -E '"Output":"(--- FAIL|    |FAIL|panic|.*\.go:[0-9]+:)' \
  | sed -E 's/.*"Output":"(.*)"}$/\1/; s/\\n$//; s/\\t/  /g; s/\\"/"/g' | head -80
tail -20 "${work}/test.stderr"
passed=$(grep -E '"Action":"pass"' "${work}/test.json" | grep -cE '"Test":"[^"/]+"' || true)
failed=$(grep -E '"Action":"fail"' "${work}/test.json" | grep -cE '"Test":"[^"/]+"' || true)
grep -E '"Action":"(pass|fail|skip)"' "${work}/test.json" | grep -E '"Test":"[^"/]+"' \
  | sed -E 's/.*"Action":"([a-z]+)".*"Test":"([^"]+)".*/\1  \2/' | sed -E 's/^pass/PASS/; s/^fail/FAIL/; s/^skip/SKIP/' | sort -k2
echo "== top-level tests: passed=${passed} failed=${failed} expected=${total}"
if [ "${passed}" -gt "${total}" ]; then total="${passed}"; fi
echo "${passed}/${total} tests passed"
echo "GRADE_TESTS {\"passed\": ${passed}, \"total\": ${total}}"
exit 0

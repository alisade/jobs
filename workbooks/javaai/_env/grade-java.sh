#!/usr/bin/env bash
# Shared grader for the Java exercise(s): copies the exercise to a temp dir, adds .grading/tests
# under src/test/java, runs `mvn -q test` with JDK 21 under a timeout, parses surefire reports.
# Last line: GRADE_TESTS {"passed": N, "total": M}. Exit 2 if the JDK/Maven toolchain is missing.
# Usage: grade-java.sh <ex_dir> <expected_total> [timeout_seconds]
set -u
ex_dir="${1:?ex_dir}"; expected="${2:-0}"; secs="${3:-300}"
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
harness_fail() { echo "HARNESS ERROR: ${1}" >&2; echo "HARNESS ERROR: ${1}"; exit 2; }
. "${env_dir}/java-env.sh" || harness_fail "JDK 21 or Maven not found. brew install openjdk@21 maven (see tools/doctor.sh javaai)."
tmp="$(mktemp -d "${TMPDIR:-/tmp}/grade-javaai-java.XXXXXX")"
trap 'rm -rf "${tmp}"' EXIT
work="${tmp}/$(basename "${ex_dir}")"
mkdir -p "${work}"
(cd "${ex_dir}" && tar --exclude ./target --exclude ./.grading -cf - .) | (cd "${work}" && tar -xf -) || harness_fail "copy failed"
if [ -d "${ex_dir}/.grading/tests" ]; then cp -R "${ex_dir}/.grading/tests/." "${work}/src/test/java/"; fi
if command -v timeout >/dev/null 2>&1; then TO=(timeout "${secs}"); else TO=(perl -e 'alarm shift; exec @ARGV' "${secs}"); fi
(cd "${work}" && "${TO[@]}" mvn -q -B -o -Dmaven.test.failure.ignore=true -Dsurefire.printSummary=false test >"${tmp}/mvn.log" 2>&1) \
  || (cd "${work}" && "${TO[@]}" mvn -q -B -Dmaven.test.failure.ignore=true test >"${tmp}/mvn.log" 2>&1)
rc=$?
reports="${work}/target/surefire-reports"
if ! ls "${reports}"/TEST-*.xml >/dev/null 2>&1; then
  grep -E 'ERROR|error:' "${tmp}/mvn.log" | head -20
  echo "compilation or build failed: every test counts as failed (mvn exit ${rc})"
  echo "GRADE_TESTS {\"passed\": 0, \"total\": ${expected}}"
  exit 0
fi
python3 - "${reports}" "${expected}" <<'PY'
import sys, glob, xml.etree.ElementTree as ET
d, expected = sys.argv[1], int(sys.argv[2])
passed = total = 0
for f in sorted(glob.glob(d + "/TEST-*.xml")):
    for tc in ET.parse(f).getroot().iter("testcase"):
        total += 1
        name = tc.get("classname", "") + "::" + tc.get("name", "")
        bad = tc.find("failure") if tc.find("failure") is not None else tc.find("error")
        if bad is not None:
            msg = (bad.get("message") or (bad.text or "")).strip().splitlines()
            print("FAIL  " + name + "  -- " + (msg[0][:200] if msg else ""))
        elif tc.find("skipped") is not None:
            print("SKIP  " + name + "  (counts as not passed)")
        else:
            passed += 1
            print("PASS  " + name)
total = max(total, expected)
print(f"{passed}/{total} tests passed")
print('GRADE_TESTS {"passed": %d, "total": %d}' % (passed, total))
PY

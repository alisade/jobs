#!/usr/bin/env bash
# Grader for ms/w2-t1. Run from the exercise folder: bash .grading/grade.sh
# Never modifies learner files: everything runs in a temp copy.
set -u

ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/grade-ms-w2-t1.XXXXXX")"
trap 'rm -rf "${tmp}"' EXIT

harness_fail() {
  echo "HARNESS ERROR: ${1}" >&2
  echo "HARNESS ERROR: ${1}"
  exit 2
}

run_to() {
  # run_to <seconds> <cmd...>: portable timeout (GNU timeout, gtimeout, or perl alarm)
  local secs="${1}"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "${secs}" "${@}"
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "${secs}" "${@}"
  else perl -e 'alarm shift; exec @ARGV' "${secs}" "${@}"; fi
}

command -v uv >/dev/null 2>&1 || harness_fail "uv not found. Run tools/doctor.sh ms for install steps."

mkdir -p "${tmp}/work"
rsync -a --exclude .venv --exclude node_modules --exclude bin --exclude obj \
  --exclude __pycache__ --exclude .pytest_cache "${ex_dir}/" "${tmp}/work/" \
  || harness_fail "could not copy exercise to temp dir"
cd "${tmp}/work" || harness_fail "temp dir missing"

if ! run_to 300 uv sync --quiet >"${tmp}/sync.log" 2>&1; then
  cat "${tmp}/sync.log" >&2
  harness_fail "uv sync failed (see above). Run tools/doctor.sh ms."
fi

echo "== running visible + hidden tests =="
PYTHONDONTWRITEBYTECODE=1 run_to 240 uv run --quiet pytest -q -p no:cacheprovider \
  --junitxml "${tmp}/junit.xml" tests .grading/tests 2>&1 | tail -n 60
[ -f "${tmp}/junit.xml" ] || harness_fail "pytest produced no report (timeout or crash)"

uv run --quiet python - "${tmp}/junit.xml" <<'PY'
import sys, json, xml.etree.ElementTree as ET
root = ET.parse(sys.argv[1]).getroot()
suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
total = passed = 0
failed = []
for s in suites:
    for tc in s.iter("testcase"):
        total += 1
        bad = [c for c in tc if c.tag in ("failure", "error")]
        skipped = [c for c in tc if c.tag == "skipped"]
        if bad or skipped:
            msg = (bad[0].get("message") if bad else "skipped") or ""
            failed.append(f"{tc.get('classname')}::{tc.get('name')}: {msg.splitlines()[0][:160] if msg else ''}")
        else:
            passed += 1
print(f"== summary: {passed}/{total} tests passed ==")
for f in failed:
    print("FAILED", f)
print("GRADE_TESTS " + json.dumps({"passed": passed, "total": total}))
PY

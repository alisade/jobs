#!/usr/bin/env bash
# Grader for ms/w6-t1. Run from the exercise folder: bash .grading/grade.sh
# Never modifies learner files: builds and tests a temp copy with the hidden tests added.
set -u

ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_proj="tests/Tailspin.Plugins.Tests/Tailspin.Plugins.Tests.csproj"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/grade-ms-w6-t1.XXXXXX")"
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

if ! command -v dotnet >/dev/null 2>&1; then
  harness_fail "dotnet SDK not found. This exercise needs the .NET SDK; tools/doctor.sh ms explains the install (brew install --cask dotnet-sdk)."
fi
command -v python3 >/dev/null 2>&1 || harness_fail "python3 not found. Run tools/doctor.sh ms."

export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1

mkdir -p "${tmp}/work"
rsync -a --exclude bin --exclude obj --exclude incident --exclude TestResults "${ex_dir}/" "${tmp}/work/" \
  || harness_fail "could not copy exercise to temp dir"
cd "${tmp}/work" || harness_fail "temp dir missing"
mkdir -p "$(dirname "${test_proj}")/Hidden"
cp .grading/tests/*.cs "$(dirname "${test_proj}")/Hidden/" || harness_fail "hidden tests missing"

# Expected test count, used if the learner's code does not compile (every test counts as failed).
expected="$(python3 - "$(dirname "${test_proj}")" <<'PY'
import pathlib, re, sys
n = 0
for f in pathlib.Path(sys.argv[1]).rglob("*.cs"):
    if "/obj/" in str(f) or "/bin/" in str(f):
        continue
    s = f.read_text()
    n += len(re.findall(r"\[Fact\b", s)) + len(re.findall(r"\[InlineData\b", s))
print(n)
PY
)"

echo "== restore =="
if ! run_to 240 dotnet restore "${test_proj}" >"${tmp}/restore.log" 2>&1; then
  tail -n 30 "${tmp}/restore.log" >&2
  harness_fail "dotnet restore failed (network or NuGet cache problem). Run make setup once online."
fi

echo "== build + visible and hidden tests =="
run_to 300 dotnet test "${test_proj}" --no-restore --logger "trx;LogFileName=results.trx" \
  --results-directory "${tmp}/results" >"${tmp}/test.log" 2>&1
grep -E "error CS|Failed |Passed!|Failed!|Total tests" "${tmp}/test.log" | head -n 60

trx="${tmp}/results/results.trx"
if [ ! -f "${trx}" ]; then
  if grep -q "error CS" "${tmp}/test.log"; then
    echo "== summary: build failed; counting all ${expected} tests as failed =="
    echo "GRADE_TESTS {\"passed\": 0, \"total\": ${expected}}"
    exit 0
  fi
  tail -n 40 "${tmp}/test.log" >&2
  harness_fail "dotnet test produced no results (timeout or crash)"
fi

python3 - "${trx}" <<'PY'
import json, sys, xml.etree.ElementTree as ET
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
root = ET.parse(sys.argv[1]).getroot()
results = root.findall(".//t:UnitTestResult", ns)
total = len(results)
passed = sum(1 for r in results if r.get("outcome") == "Passed")
print(f"== summary: {passed}/{total} tests passed ==")
for r in results:
    if r.get("outcome") != "Passed":
        msg = r.find(".//t:Message", ns)
        text = (msg.text or "").strip().splitlines()[0][:160] if msg is not None and msg.text else r.get("outcome")
        print(f"FAILED {r.get('testName')}: {text}")
print("GRADE_TESTS " + json.dumps({"passed": passed, "total": total}))
PY

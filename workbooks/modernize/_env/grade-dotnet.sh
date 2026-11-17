#!/usr/bin/env bash
# Shared grader for .NET exercises: copies the exercise to a temp dir (the learner's folder is never
# written to), adds .grading/tests/*.cs to the test project under Hidden/, runs dotnet test offline
# against the NuGet cache that make setup filled, parses the trx. Last line: GRADE_TESTS {...}.
# Usage: grade-dotnet.sh <ex_dir> <test_proj_relative_path> [timeout_seconds]
set -u
ex_dir="${1:?ex_dir}"; test_proj="${2:?test project}"; secs="${3:-300}"
harness_fail() { echo "HARNESS ERROR: ${1}" >&2; echo "HARNESS ERROR: ${1}"; exit 2; }
run_to() {
  local s="${1}"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "${s}" "${@}"
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "${s}" "${@}"
  else perl -e 'alarm shift; exec @ARGV' "${s}" "${@}"; fi
}
command -v dotnet >/dev/null 2>&1 || harness_fail "dotnet SDK not found (brew install --cask dotnet-sdk; see tools/doctor.sh modernize)."
export DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1
tmp="$(mktemp -d "${TMPDIR:-/tmp}/grade-modernize-dotnet.XXXXXX")"
trap 'rm -rf "${tmp}"' EXIT
mkdir -p "${tmp}/work"
rsync -a --exclude bin --exclude obj --exclude TestResults --exclude .grading "${ex_dir}/" "${tmp}/work/" || harness_fail "copy failed"
cd "${tmp}/work" || harness_fail "temp dir missing"
proj_dir="$(dirname "${test_proj}")"
[ -f "${test_proj}" ] || harness_fail "test project ${test_proj} not found"
mkdir -p "${proj_dir}/Hidden"
cp "${ex_dir}"/.grading/tests/*.cs "${proj_dir}/Hidden/" 2>/dev/null || true
expected="$(python3 - "${proj_dir}" <<'PY'
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
echo "== restore (offline, from the NuGet cache) =="
if ! run_to 240 dotnet restore "${test_proj}" --source "${HOME}/.nuget/packages" >"${tmp}/restore.log" 2>&1; then
  if grep -q "error CS\|error MSB" "${tmp}/restore.log" && ! grep -q "NU1101\|NU1102\|NU1301" "${tmp}/restore.log"; then
    echo "== project file does not load; counting all ${expected} tests as failed =="
    grep -E "error" "${tmp}/restore.log" | head -10
    echo "GRADE_TESTS {\"passed\": 0, \"total\": ${expected}}"; exit 0
  fi
  tail -n 20 "${tmp}/restore.log" >&2
  harness_fail "dotnet restore failed offline. Run make setup once while online so NuGet caches the packages."
fi
echo "== build + visible and hidden tests =="
run_to "${secs}" dotnet test "${test_proj}" --no-restore --logger "trx;LogFileName=results.trx" \
  --results-directory "${tmp}/results" >"${tmp}/test.log" 2>&1
grep -E "error CS|Failed |Passed!|Failed!|Total tests" "${tmp}/test.log" | sort -u | head -n 40
trx="${tmp}/results/results.trx"
if [ ! -f "${trx}" ]; then
  if grep -q "error CS\|error MSB\|error NETSDK" "${tmp}/test.log"; then
    echo "== build failed; counting all ${expected} tests as failed =="
    echo "GRADE_TESTS {\"passed\": 0, \"total\": ${expected}}"; exit 0
  fi
  tail -n 40 "${tmp}/test.log" >&2
  harness_fail "dotnet test produced no results (timeout or crash)"
fi
python3 - "${trx}" "${expected}" <<'PY'
import json, sys, xml.etree.ElementTree as ET
ns = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}
root = ET.parse(sys.argv[1]).getroot()
results = root.findall(".//t:UnitTestResult", ns)
passed = sum(1 for r in results if r.get("outcome") == "Passed")
for r in results:
    if r.get("outcome") == "Passed":
        print(f"PASS  {r.get('testName')}")
    else:
        msg = r.find(".//t:Message", ns)
        text = (msg.text or "").strip().splitlines()[0][:160] if msg is not None and msg.text else r.get("outcome")
        print(f"FAIL  {r.get('testName')}  -- {text}")
total = max(len(results), int(sys.argv[2]))
print(f"{passed}/{total} tests passed")
print("GRADE_TESTS " + json.dumps({"passed": passed, "total": total}))
PY

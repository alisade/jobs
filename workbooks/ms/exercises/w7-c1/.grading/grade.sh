#!/usr/bin/env bash
# Grader for ms/w7-c1. Run from the exercise folder: bash .grading/grade.sh
# Never modifies learner files: everything runs in a temp copy.
set -u

ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp="$(mktemp -d "${TMPDIR:-/tmp}/grade-ms-w7c1.XXXXXX")"
trap 'rm -rf "${tmp}"' EXIT

harness_fail() {
  echo "HARNESS ERROR: ${1}" >&2
  echo "HARNESS ERROR: ${1}"
  exit 2
}

run_to() {
  local secs="${1}"; shift
  if command -v timeout >/dev/null 2>&1; then timeout "${secs}" "${@}"
  elif command -v gtimeout >/dev/null 2>&1; then gtimeout "${secs}" "${@}"
  else perl -e 'alarm shift; exec @ARGV' "${secs}" "${@}"; fi
}

command -v node >/dev/null 2>&1 || harness_fail "node not found. Run tools/doctor.sh ms for install steps."
command -v npm >/dev/null 2>&1 || harness_fail "npm not found. Run tools/doctor.sh ms for install steps."

mkdir -p "${tmp}/work"
rsync -a --exclude node_modules --exclude .venv --exclude bin --exclude obj \
  "${ex_dir}/" "${tmp}/work/" || harness_fail "could not copy exercise to temp dir"
cd "${tmp}/work" || harness_fail "temp dir missing"
mkdir -p tests/__hidden__
cp .grading/tests/*.ts tests/__hidden__/ || harness_fail "hidden tests missing"

if [ -d "${ex_dir}/node_modules" ]; then
  ln -s "${ex_dir}/node_modules" node_modules
else
  if ! run_to 240 npm ci --prefer-offline --no-audit --no-fund >"${tmp}/npm.log" 2>&1; then
    tail -n 30 "${tmp}/npm.log" >&2
    harness_fail "npm ci failed (see above). Run tools/doctor.sh ms."
  fi
fi

echo "== running visible + hidden jest tests =="
run_to 240 npx jest --ci --json --outputFile="${tmp}/jest.json" >"${tmp}/jest.log" 2>&1
tail -n 60 "${tmp}/jest.log"
[ -s "${tmp}/jest.json" ] || harness_fail "jest produced no report (timeout or crash)"

node - "${tmp}/jest.json" <<'JS'
const r = require(process.argv[2]);
let total = 0, passed = 0;
const failed = [];
for (const file of r.testResults) {
  if (file.assertionResults.length === 0 && file.status === "failed") {
    // A suite that fails to compile/run: count every test( it declares as failed.
    const src = require("fs").readFileSync(file.name, "utf8");
    const n = Math.max(1, (src.match(/^\s*test\(/gm) || []).length);
    total += n;
    const msg = (file.message || "").split("\n").map(l => l.trim()).filter(l => l && !l.startsWith("\u25cf")).slice(0, 2).join(" | ");
    failed.push(file.name.split("/tests/")[1] + ": suite failed to run (" + n + " tests counted as failed): " + msg.slice(0, 200));
  }
  for (const a of file.assertionResults) {
    total += 1;
    if (a.status === "passed") passed += 1;
    else failed.push(a.fullName + ": " + ((a.failureMessages[0] || a.status).split("\n")[0]).slice(0, 160));
  }
}
console.log(`== summary: ${passed}/${total} tests passed ==`);
for (const f of failed) console.log("FAILED " + f);
console.log(`GRADE_TESTS {"passed": ${passed}, "total": ${total}}`);
JS

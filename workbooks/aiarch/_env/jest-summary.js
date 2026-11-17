"use strict";
// Summarize a jest --json report: one PASS/FAIL line per test, then GRADE_TESTS.
// A suite that fails to compile counts each test( / it( it declares as failed, and the total is
// never below the exercise's expected total, so a learner file that does not import still
// reports the full denominator.
const fs = require("fs");
const [, , file, expectedArg] = process.argv;
const r = JSON.parse(fs.readFileSync(file, "utf8"));
const expected = Number(expectedArg || 0);
let total = 0;
let passed = 0;
const lines = [];
for (const suite of r.testResults) {
  const rel = suite.name.replace(/^.*?\/tests\//, "tests/");
  if (suite.assertionResults.length === 0 && suite.status === "failed") {
    let n = 1;
    try {
      const src = fs.readFileSync(suite.name, "utf8");
      n = Math.max(1, (src.match(/^\s*(test|it)(\.each\([^)]*\))?\(/gm) || []).length);
    } catch { /* keep 1 */ }
    total += n;
    const msg = (suite.message || "").split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("\u25cf")).slice(0, 2).join(" | ");
    lines.push(`FAIL  ${rel}: suite failed to run (${n} tests counted as failed) -- ${msg.slice(0, 220)}`);
  }
  for (const a of suite.assertionResults) {
    total += 1;
    if (a.status === "passed") {
      passed += 1;
      lines.push(`PASS  ${rel} :: ${a.fullName}`);
    } else {
      const m = (a.failureMessages[0] || a.status).split("\n").map((l) => l.trim()).filter(Boolean)[0] || a.status;
      lines.push(`FAIL  ${rel} :: ${a.fullName} -- ${m.replace(/\u001b\[[0-9;]*m/g, "").slice(0, 200)}`);
    }
  }
}
console.log(lines.join("\n"));
total = Math.max(total, expected);
console.log(`${passed}/${total} tests passed`);
console.log(`GRADE_TESTS {"passed": ${passed}, "total": ${total}}`);

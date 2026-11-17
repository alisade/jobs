// Visible tests for connect/w4-t1. The grader adds more dates and guards.
/* eslint-disable @typescript-eslint/no-var-requires */
const { runSuite, report, load } = require("../tools/validate");
const { toLocal } = require("../tools/hours");

test("validation suite is green for Fri 2026-10-09 (the parallel-run day)", () => {
  const bad = runSuite(["2026-10-09"]).filter((r: any) => !r.same);
  expect(bad.length === 0 ? "" : report(bad).split("\n").slice(0, 6).join("\n")).toBe("");
});

test("every hours of operation resource uses a valid IANA time zone", () => {
  for (const h of load().hours) expect(() => toLocal("2026-10-09T12:00:00Z", h.TimeZone)).not.toThrow();
});

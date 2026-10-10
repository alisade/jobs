// Hidden tests for connect/w4-t1.
/* eslint-disable @typescript-eslint/no-var-requires */
const { runSuite, report, load } = require("../../tools/validate");

const green = (dates: string[]) => {
  const bad = runSuite(dates).filter((r: any) => !r.same);
  return bad.length === 0 ? "" : report(bad).split("\n").slice(0, 6).join("\n");
};

test("Columbus Day 2026-10-12 (holiday override) stays green", () => expect(green(["2026-10-12"])).toBe(""));
test("Tue 2026-10-13 is green", () => expect(green(["2026-10-13"])).toBe(""));
test("after the DST change: Mon 2026-11-02 is green (a fixed UTC offset is not a fix)", () => expect(green(["2026-11-02"])).toBe(""));
test("after the spring DST change: Mon 2026-03-09 is green", () => expect(green(["2026-03-09"])).toBe(""));
test("Thanksgiving 2026-11-26/27 is green", () => expect(green(["2026-11-26", "2026-11-27"])).toBe(""));

describe("guards: fix the cause, not the symptom", () => {
  const env = load();
  const hoo = env.hours.find((h: any) => h.Name === "HelpDeskHours");
  test("HelpDeskHours still 06:00-20:00 local, 7 days (hours not shifted to compensate)", () => {
    expect(hoo.Config).toHaveLength(7);
    for (const c of hoo.Config) {
      expect(c.StartTime).toEqual({ Hours: 6, Minutes: 0 });
      expect(c.EndTime).toEqual({ Hours: 20, Minutes: 0 });
    }
  });
  test("holiday overrides are all still there", () => {
    expect(env.overrides.filter((o: any) => o.HoursOfOperationId === "hoo-helpdesk-holidays")).toHaveLength(7);
  });
  test("the migrated flow still checks the holiday hours and then the help desk hours", () => {
    const ids = env.flow.Actions.filter((a: any) => a.Type === "CheckHoursOfOperation").map((a: any) => a.Parameters.HoursOfOperationId.split("/").pop());
    expect(ids).toEqual(expect.arrayContaining(["hoo-helpdesk", "hoo-helpdesk-holidays"]));
  });
});

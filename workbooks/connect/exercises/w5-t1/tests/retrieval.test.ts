// Visible checks for connect/w5-t1. The grader adds more.
import { ask, callers, forbidden, traffic } from "./harness";

test("a Finance employee finds the Finance drive article", async () => {
  const { ids } = await ask("fin-uk", "map the finance drive");
  expect(ids[0]).toBe("KB0020456");
});

test("replayed traffic returns nothing a caller is not entitled to", async () => {
  const leaks: string[] = [];
  for (const t of traffic.traffic) {
    const { r } = await ask(t.caller, t.query);
    for (const x of r.results) if (forbidden(callers[t.caller], x.metadata)) leaks.push(`${t.caller} "${t.query}" -> ${x.metadata.articleId}`);
  }
  expect(leaks).toEqual([]);
});

test("an empty filtered result is not retried without the filter", async () => {
  const { calls, r } = await ask("it-in", "change my bank account for payroll");
  expect(calls.length).toBe(1);
  expect(r.status).toBe("NO_ARTICLES");
});

// Visible tests for connect/w8-c1. The grader adds more (edge cases, failure paths).
import { promote } from "../src/promote";
import { devExport, env, parse } from "./harness";

test("promoting to test succeeds and produces an artifact for every flow and module", () => {
  const r = promote(devExport(), env("test"));
  expect(r.problems).toEqual([]);
  expect(r.ok).toBe(true);
  expect(r.artifacts.map((a) => a.name).sort()).toEqual(["LFG Help Desk Inbound", "LFG Major Incident", "mod-after-hours", "mod-password-reset"]);
});

test("queue ARNs are rewritten to the target environment", () => {
  const prod = env("prod");
  const r = promote(devExport(), prod);
  const major = parse(r.artifacts.find((a) => a.name === "LFG Major Incident")!.content);
  const q = major.Actions.find((a: any) => a.Identifier === "set-q-major").Parameters.QueueId;
  expect(q).toBe(prod.resources.find((x) => x.kind === "queue" && x.name === "MajorIncident")!.arn);
});

test("no artifact for prod mentions the dev account", () => {
  const r = promote(devExport(), env("prod"));
  expect(r.ok).toBe(true);
  for (const a of r.artifacts) expect(a.content).not.toContain("111122223333");
});

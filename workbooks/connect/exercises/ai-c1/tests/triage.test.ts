// Visible tests for connect/ai-c1. The grader adds more (guards, failure paths, eval metrics).
import { buildRequest, triage, toConnectAttributes, SYSTEM_PROMPT } from "../src/triage";
import { runEval } from "../src/eval";
import { replay, transcriptOf, cases } from "./helpers";

test("the caller transcript goes in the user turn inside <transcript> tags, never in the system prompt", () => {
  const t = transcriptOf("pw-basic");
  const req = buildRequest(t);
  expect(JSON.stringify(req.system)).not.toContain("locked out");
  expect(req.messages[0].content[0].text).toContain("<transcript>");
  expect(req.messages[0].content[0].text).toContain(t);
  expect(req.inferenceConfig.temperature).toBe(0);
  expect(req.system[0].text).toBe(SYSTEM_PROMPT);
});

test("a clean password reset is triaged from the model", async () => {
  const { client } = replay();
  const r = await triage(transcriptOf("pw-basic"), client);
  expect(r).toMatchObject({ category: "password_reset", priority: "P3", source: "model" });
});

test("Connect attributes are a flat map of strings", async () => {
  const { client } = replay();
  const attrs = toConnectAttributes(await triage(transcriptOf("hw-laptop"), client));
  for (const v of Object.values(attrs)) expect(typeof v).toBe("string");
  expect(attrs.triageCategory).toBe("hardware");
});

test("runEval reports accuracy over all cases", async () => {
  const stub = async () => ({ category: "password_reset" as const, priority: "P3" as const, summary: "", needsHuman: false, source: "model" as const });
  const report = await runEval(cases.slice(0, 2), stub);
  expect(report.total).toBe(2);
  expect(report.accuracy).toBe(1);
});

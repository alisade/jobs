// Visible tests for connect/w6-c2. The grader adds hidden tests.
import { ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { redactPii } from "../src/redact";
import { buildConverseInput, parseConverseOutput } from "../src/summarize";
import { evaluateSummary } from "../src/eval";
import { makeHandler } from "../src/handler";
import { config, converse, event, evalCases, setup } from "./helpers";

test("redacts a Luhn-valid card number but not ticket or employee ids", () => {
  const r = redactPii("Card 4111 1111 1111 1111, incident INC0041877, employee E20417");
  expect(r.text).toBe("Card [CREDIT_DEBIT_NUMBER], incident INC0041877, employee E20417");
  expect(r.entities).toEqual(["CREDIT_DEBIT_NUMBER"]);
});

test("the Converse request forces the summary tool and applies the guardrail", () => {
  const i = buildConverseInput("AGENT: hi", config);
  expect(i.modelId).toBe(config.modelId);
  expect(i.toolConfig!.toolChoice).toEqual({ tool: { name: "record_acw_summary" } });
  expect(i.guardrailConfig).toMatchObject({ guardrailIdentifier: "gr-lfg-acw-summary", guardrailVersion: "4" });
});

test("a tool_use response parses into a summary", () => {
  const o = parseConverseOutput(converse(1));
  expect(o.status).toBe("OK");
});

test("the eval passes a faithful summary", () => {
  const c = evalCases()[0];
  expect(evaluateSummary(c.candidate, c.transcript, c.reference).pass).toBe(true);
});

test("end to end: a disconnected voice contact gets a work note and contact attributes", async () => {
  const s = setup();
  const r = await makeHandler(s.deps as any)(event("disconnected-1-voice"));
  expect(r).toMatchObject({ status: "OK", wroteWorkNote: true });
  expect(s.notes).toHaveLength(1);
  expect(s.bedrock.commandCalls(ConverseCommand)).toHaveLength(1);
});

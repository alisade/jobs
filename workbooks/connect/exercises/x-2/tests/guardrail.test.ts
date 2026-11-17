// Visible tests for connect/x-2. The grader adds more.
import { mockClient } from "aws-sdk-client-mock";
import { BedrockRuntimeClient, ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { evaluate } from "../src/evaluator";
import { answer, configFromEnv } from "../src/selfService";
import { cases, config, env, topicLimitErrors } from "./harness";

test("guardrail config respects the CreateGuardrail topic limits", () => {
  expect(topicLimitErrors(config())).toEqual([]);
});

test("every pen-test attack case is still blocked (PT-2026-17 must stay closed)", () => {
  const cfg = config();
  const missed = cases().filter((c) => c.expect === "BLOCK" && !evaluate(cfg, c.input).blocked).map((c) => c.input);
  expect(missed).toEqual([]);
});

test("the Lambda sends a pinned guardrail version with tracing on", async () => {
  const br = mockClient(BedrockRuntimeClient);
  br.on(ConverseCommand).resolves({ stopReason: "end_turn", output: { message: { role: "assistant", content: [{ text: "ok" }] } } } as any);
  const cfg = configFromEnv(env());
  await answer(new BedrockRuntimeClient({ region: "us-east-1" }), cfg, { contactId: "c1", text: "hello" });
  const g = br.commandCalls(ConverseCommand)[0].args[0].input.guardrailConfig!;
  expect(g.guardrailIdentifier).toBe("gr7k2m9q4xld");
  expect(g.guardrailVersion).toMatch(/^\d+$/);
  expect(g.trace).toBe("enabled");
  br.restore();
});

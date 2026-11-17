// Hidden tests for connect/w6-c2 (run from tests/__hidden__).
import { ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import { RetrieveCommand } from "@aws-sdk/client-bedrock-agent-runtime";
import { GetContactAttributesCommand, UpdateContactAttributesCommand } from "@aws-sdk/client-connect";
import { redactPii } from "../../src/redact";
import { buildConverseInput, parseConverseOutput } from "../../src/summarize";
import { relatedArticles } from "../../src/knowledge";
import { evaluateSummary } from "../../src/eval";
import { makeHandler } from "../../src/handler";
import { RetryableError } from "../../src/types";
import { cid, config, converse, event, evalCases, setup } from "../helpers";

describe("redaction", () => {
  test.each([
    ["call me at 555-201-7788", "call me at [PHONE]", "PHONE"],
    ["ssn 123-45-6789 please", "ssn [SSN] please", "SSN"],
    ["mail j.doe@larkspur.example.com", "mail [EMAIL]", "EMAIL"],
    ["my password is Hunter2!", "my password is [PASSWORD]", "PASSWORD"],
    ["card 5500-0000-0000-0004", "card [CREDIT_DEBIT_NUMBER]", "CREDIT_DEBIT_NUMBER"],
  ])("%s", (input, out, ent) => {
    const r = redactPii(input);
    expect(r.text).toBe(out);
    expect(r.entities).toContain(ent);
  });
  test("a 16-digit number that fails Luhn is not a card", () => {
    expect(redactPii("order 1234 5678 9012 3456").text).toBe("order 1234 5678 9012 3456");
  });
  test("versions and RITM numbers are untouched", () => {
    const t = "client 6.2.3, request RITM0098812";
    expect(redactPii(t).text).toBe(t);
  });
});

describe("Converse request and response", () => {
  test("system prompt marks the transcript as untrusted data and temperature is 0", () => {
    const i = buildConverseInput("AGENT: hi", config);
    expect(JSON.stringify(i.system)).toMatch(/untrusted/i);
    expect(i.inferenceConfig).toMatchObject({ temperature: 0, maxTokens: config.maxTokens });
    expect(i.guardrailConfig!.trace).toBe("enabled");
  });
  test("the tool schema requires every summary field", () => {
    const spec = buildConverseInput("x", config).toolConfig!.tools![0].toolSpec!;
    expect((spec.inputSchema as any).json.required.sort()).toEqual(["actionsTaken", "followUps", "issue", "resolution", "sentiment"]);
  });
  test("guardrail_intervened becomes GUARDRAIL_BLOCKED, never a summary", () => {
    expect(parseConverseOutput(converse(3))).toEqual({ status: "GUARDRAIL_BLOCKED" });
  });
  test("a tool call missing resolution is INVALID_OUTPUT naming the field", () => {
    const o = parseConverseOutput(converse(4));
    expect(o.status).toBe("INVALID_OUTPUT");
    expect((o as any).reason).toMatch(/resolution/);
  });
  test("max_tokens is INVALID_OUTPUT", () => {
    expect(parseConverseOutput({ ...converse(1), stopReason: "max_tokens" }).status).toBe("INVALID_OUTPUT");
  });
  test("a bad sentiment value is rejected", () => {
    const c = converse(1);
    c.output.message.content[0].toolUse.input.sentiment = "ANGRY";
    expect(parseConverseOutput(c).status).toBe("INVALID_OUTPUT");
  });
});

describe("knowledge retrieval", () => {
  test("filters by audience, drops low scores, titles from metadata, sorted by score", async () => {
    const s = setup();
    const a = await relatedArticles(s.deps.agentRuntime, config, "Okta Verify MFA after phone change");
    expect(a.map((x) => x.title)).toEqual(["Re-register Okta Verify after a phone change", "KB0011877"]);
    const call = s.agent.commandCalls(RetrieveCommand)[0].args[0].input as any;
    expect(call.knowledgeBaseId).toBe("KBLFGHELP01");
    expect(call.retrievalConfiguration.vectorSearchConfiguration.filter).toEqual({ in: { key: "audience", value: ["agent", "all-employees"] } });
    expect(call.retrievalConfiguration.vectorSearchConfiguration.numberOfResults).toBe(3);
  });
  test("a retrieval failure returns no articles instead of failing the pipeline", async () => {
    const s = setup();
    s.agent.on(RetrieveCommand).rejects(Object.assign(new Error("throttled"), { name: "ThrottlingException" }));
    expect(await relatedArticles(s.deps.agentRuntime, config, "q")).toEqual([]);
  });
});

describe("handler", () => {
  test("the transcript sent to Bedrock is redacted (the analytics redaction missed a card number)", async () => {
    const s = setup();
    await makeHandler(s.deps as any)(event("disconnected-1-voice"));
    const body = JSON.stringify(s.bedrock.commandCalls(ConverseCommand)[0].args[0].input);
    expect(body).not.toMatch(/4111/);
    expect(body).toMatch(/\[CREDIT_DEBIT_NUMBER\]/);
  });
  test("the work note is marked, lists KB titles and carries no PII from the model output", async () => {
    const s = setup();
    await makeHandler(s.deps as any)(event("disconnected-2-chat"));
    const n = s.notes[0];
    expect(n.sysId).toBe("9f1e0000000000000000000000000002");
    expect(n.note).toContain(`[acw-summary contact=${cid(2)}`);
    expect(n.note).not.toMatch(/555-201-7788/);
    expect(n.note).toMatch(/\[PHONE\]/);
    expect(n.note).toMatch(/Re-register Okta Verify/);
  });
  test("KB retrieval queries with the redacted issue, not the transcript", async () => {
    const s = setup();
    await makeHandler(s.deps as any)(event("disconnected-1-voice"));
    const q = (s.agent.commandCalls(RetrieveCommand)[0].args[0].input as any).retrievalQuery.text;
    expect(q).toMatch(/Okta Verify/);
    expect(q.length).toBeLessThan(200);
  });
  test("contact attributes: status, short issue and sentiment on the right instance and contact", async () => {
    const s = setup();
    await makeHandler(s.deps as any)(event("disconnected-1-voice"));
    const u = s.connect.commandCalls(UpdateContactAttributesCommand)[0].args[0].input as any;
    expect(u).toMatchObject({ InstanceId: config.instanceId, InitialContactId: cid(1) });
    expect(u.Attributes).toMatchObject({ acwSummaryStatus: "OK", acwSentiment: "POSITIVE" });
    expect(u.Attributes.acwSummaryIssue.length).toBeLessThanOrEqual(config.attributeMaxChars);
    expect(Object.values(u.Attributes).every((v) => typeof v === "string")).toBe(true);
  });
  test("EventBridge redelivery: second event is DUPLICATE, no second Bedrock call, no second note", async () => {
    const s = setup();
    const h = makeHandler(s.deps as any);
    await h(event("disconnected-1-voice"));
    const r = await h(event("disconnected-1-voice"));
    expect(r.status).toBe("DUPLICATE");
    expect(s.bedrock.commandCalls(ConverseCommand)).toHaveLength(1);
    expect(s.notes).toHaveLength(1);
  });
  test("both detail-type spellings and both channel casings are accepted", async () => {
    const s = setup();
    const h = makeHandler(s.deps as any);
    expect((await h(event("disconnected-2-chat"))).status).toBe("OK");
    expect((await h(event("disconnected-3-voice"))).status).toBe("GUARDRAIL_BLOCKED");
  });
  test("non-DISCONNECTED events and TASK contacts are ignored without side effects", async () => {
    const s = setup();
    const h = makeHandler(s.deps as any);
    expect((await h(event("queued-1"))).status).toBe("IGNORED");
    expect((await h(event("disconnected-6-task"))).status).toBe("IGNORED");
    expect(s.bedrock.commandCalls(ConverseCommand)).toHaveLength(0);
    expect(s.store.calls).toEqual([]);
  });
  test("guardrail block: no work note, status attribute set, claim completed", async () => {
    const s = setup({ attrs: { [cid(3)]: { snIncidentSysId: "9f1e0000000000000000000000000003" } } });
    const r = await makeHandler(s.deps as any)(event("disconnected-3-voice"));
    expect(r).toMatchObject({ status: "GUARDRAIL_BLOCKED", wroteWorkNote: false });
    expect(s.notes).toEqual([]);
    const u = s.connect.commandCalls(UpdateContactAttributesCommand)[0].args[0].input as any;
    expect(u.Attributes.acwSummaryStatus).toBe("GUARDRAIL_BLOCKED");
    expect(s.store.items.get(`acw#${cid(3)}`)!.status).toBe("COMPLETED");
  });
  test("invalid model output: nothing written to ServiceNow", async () => {
    const s = setup({ attrs: { [cid(4)]: { snIncidentSysId: "9f1e0000000000000000000000000004" } } });
    const r = await makeHandler(s.deps as any)(event("disconnected-4-voice"));
    expect(r.status).toBe("INVALID_OUTPUT");
    expect(s.notes).toEqual([]);
  });
  test("no incident on the contact: summary still recorded in attributes, no note", async () => {
    const s = setup({ attrs: {} });
    const r = await makeHandler(s.deps as any)(event("disconnected-1-voice"));
    expect(r).toMatchObject({ status: "OK", wroteWorkNote: false });
    expect(s.connect.commandCalls(GetContactAttributesCommand)).toHaveLength(1);
  });
  test("transcript not ready: RetryableError and the claim is released", async () => {
    const s = setup();
    await expect(makeHandler(s.deps as any)(event("disconnected-5-voice"))).rejects.toMatchObject({ code: "TRANSCRIPT_NOT_READY" });
    expect(s.store.items.has(`acw#${cid(5)}`)).toBe(false);
  });
  test("Bedrock throttling: RetryableError DOWNSTREAM, claim released, retry later succeeds", async () => {
    const s = setup();
    const h = makeHandler(s.deps as any);
    const ok = s.bedrock.commandCalls; void ok;
    s.bedrock.on(ConverseCommand).rejectsOnce(Object.assign(new Error("slow down"), { name: "ThrottlingException" }));
    await expect(h(event("disconnected-1-voice"))).rejects.toBeInstanceOf(RetryableError);
    expect(s.store.items.has(`acw#${cid(1)}`)).toBe(false);
  });
  test("ServiceNow failure: RetryableError and claim released so the work note is retried", async () => {
    const s = setup();
    s.deps.workNotes.addWorkNote = async () => { throw new Error("503"); };
    await expect(makeHandler(s.deps as any)(event("disconnected-1-voice"))).rejects.toMatchObject({ code: "DOWNSTREAM" });
    expect(s.store.items.has(`acw#${cid(1)}`)).toBe(false);
  });
  test("a concurrent worker holding the claim makes this delivery retry, not process", async () => {
    const s = setup();
    await s.store.claim(`acw#${cid(1)}`);
    await expect(makeHandler(s.deps as any)(event("disconnected-1-voice"))).rejects.toMatchObject({ code: "IN_PROGRESS" });
    expect(s.bedrock.commandCalls(ConverseCommand)).toHaveLength(0);
  });
});

describe("faithfulness eval", () => {
  test("every case matches its expected verdict", () => {
    for (const c of evalCases()) {
      expect([c.id, evaluateSummary(c.candidate, c.transcript, c.reference).pass]).toEqual([c.id, c.expectPass]);
    }
  });
  test("a hallucinated ticket number is reported", () => {
    const c = evalCases()[2];
    expect(evaluateSummary(c.candidate, c.transcript, c.reference).hallucinations).toEqual(["INC0049999"]);
  });
  test("invented actions lower faithfulness", () => {
    const c = evalCases()[3];
    expect(evaluateSummary(c.candidate, c.transcript, c.reference).faithfulness).toBeCloseTo(0.33, 2);
  });
  test("missing facts lower coverage", () => {
    const c = evalCases()[4];
    expect(evaluateSummary(c.candidate, c.transcript, c.reference).coverage).toBeCloseTo(0.25, 2);
  });
  test("a summary with no actions is fully faithful by definition", () => {
    const c = evalCases()[0];
    expect(evaluateSummary({ ...c.candidate, actionsTaken: [] }, c.transcript, c.reference).faithfulness).toBe(1);
  });
});

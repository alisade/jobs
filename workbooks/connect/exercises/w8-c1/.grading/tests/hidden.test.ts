// Hidden tests for connect/w8-c1 (copied to tests/__hidden__ by the grader).
import * as fs from "fs";
import * as path from "path";
import { validateFlow } from "connect-kit";
import { promote } from "../../src/promote";
import { devExport, env, parse } from "../harness";

const expected = (name: string) => JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", `expected-${name}.json`), "utf8"));
const art = (r: any, name: string) => r.artifacts.find((a: any) => a.name === name);
const act = (flow: any, id: string) => flow.Actions.find((a: any) => a.Identifier === id);
const res = (inv: any, kind: string, name: string) => inv.resources.find((x: any) => x.kind === kind && x.name === name);

describe("rewriting", () => {
  test.each(["prod", "dr"])("%s: every flow and module Actions array equals the expected target content", (name) => {
    const r = promote(devExport(), env(name));
    expect(r.ok).toBe(true);
    const exp = expected(name);
    for (const [flowName, flow] of Object.entries<any>(exp.flows)) expect(parse(art(r, flowName).content).Actions).toEqual(flow.Actions);
    for (const [modName, mod] of Object.entries<any>(exp.modules)) expect(parse(art(r, modName).content).Actions).toEqual(mod.Actions);
  });
  test("Lambda qualifier (:live) is preserved", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const arn = act(parse(art(r, "mod-password-reset").content), "reset-lambda").Parameters.LambdaFunctionARN;
    expect(arn).toBe(res(prod, "lambda", "lfg-password-reset").arn + ":live");
  });
  test("Lex V2 bot alias ARN is rewritten", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const p = act(parse(art(r, "LFG Help Desk Inbound").content), "ask-bot").Parameters;
    expect(p.LexV2Bot.AliasArn).toBe(res(prod, "lexAlias", "HelpDeskBot/live").arn);
  });
  test("bare resource ids (FlowModuleId, LambdaInvocationAttributes) are rewritten", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const f = parse(art(r, "LFG Help Desk Inbound").content);
    expect(act(f, "password-module").Parameters.FlowModuleId).toBe(res(prod, "module", "mod-password-reset").id);
    expect(act(f, "identify-caller").Parameters.LambdaInvocationAttributes.callbackQueueId).toBe(res(prod, "queue", "CallbackQueue").id);
    expect(act(f, "identify-caller").Parameters.LambdaInvocationAttributes.instanceArn).toBe(prod.instanceArn);
  });
  test("ARNs embedded inside a larger string are rewritten (audit JSON in an attribute)", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const audit = act(parse(art(r, "mod-password-reset").content), "reset-lambda").Parameters.LambdaInvocationAttributes.audit;
    expect(audit).toBe(JSON.stringify({ source: "ivr", instance: prod.instanceArn }).replace(/,/, ","));
  });
  test("Metadata (canvas ActionMetadata) is rewritten too, so the console shows the right queue", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const f = parse(art(r, "LFG Help Desk Inbound").content);
    expect(f.Metadata.ActionMetadata["set-q-vip"].queue.id).toBe(res(prod, "queue", "VIPDesk").arn);
    expect(r.replacements.some((x: any) => x.artifact === "LFG Help Desk Inbound" && x.path.startsWith("$.Metadata"))).toBe(true);
  });
  test("TransferToFlow target flow ARN is rewritten", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    expect(act(parse(art(r, "LFG Help Desk Inbound").content), "to-major-incident").Parameters.ContactFlowId).toBe(res(prod, "flow", "LFG Major Incident").arn);
  });
  test("cross-region (DR us-west-2): nothing still says us-east-1 or a dev id", () => {
    const r = promote(devExport(), env("dr"));
    const devIds = devExport().inventory.resources.map((x) => x.id).filter(Boolean) as string[];
    for (const a of r.artifacts) {
      expect(a.content).not.toMatch(/us-east-1/);
      for (const id of devIds) expect(a.content).not.toContain(id);
    }
  });
  test("the input export is not mutated", () => {
    const e = devExport();
    const before = JSON.stringify(e);
    promote(e, env("prod"));
    expect(JSON.stringify(e)).toBe(before);
  });
});

describe("artifacts and report", () => {
  test("modules come before flows (a flow cannot reference a module that is not deployed yet)", () => {
    const r = promote(devExport(), env("prod"));
    const kinds = r.artifacts.map((a: any) => a.kind);
    expect(kinds.lastIndexOf("module")).toBeLessThan(kinds.indexOf("flow"));
  });
  test("artifacts carry the target id/ARN of the same-named flow or module", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const a = art(r, "mod-after-hours");
    expect(a.targetId).toBe(res(prod, "module", "mod-after-hours").id);
    expect(art(r, "LFG Help Desk Inbound").targetArn).toBe(res(prod, "flow", "LFG Help Desk Inbound").arn);
    expect(art(r, "LFG Help Desk Inbound").type).toBe("CONTACT_FLOW");
  });
  test("every output flow still passes connect-kit validateFlow", () => {
    const r = promote(devExport(), env("prod"));
    for (const a of r.artifacts.filter((x: any) => x.kind === "flow")) {
      const flow = parse(a.content);
      // resetStatus is set inside the password-reset module (invisible to a single-flow check);
      // connect-kit treats TransferToFlow as needing a NextAction, which the flow language does not.
      const v = validateFlow(flow, { knownAttributes: ["resetStatus"] });
      const transferToFlow = new Set(flow.Actions.filter((x: any) => x.Type === "TransferToFlow").map((x: any) => x.Identifier));
      expect(v.issues.filter((i) => i.severity === "error" && !(i.code === "DEAD_END" && transferToFlow.has(i.actionId)))).toEqual([]);
    }
  });
  test("content is a serialized JSON string (the API takes Content as a string)", () => {
    const r = promote(devExport(), env("prod"));
    for (const a of r.artifacts) expect(typeof a.content).toBe("string");
  });
  test("the report lists each replacement with path, from, to and the logical resource", () => {
    const prod = env("prod");
    const r = promote(devExport(), prod);
    const hit = r.replacements.find((x: any) => x.artifact === "LFG Major Incident" && x.path === "$.Actions[0].Parameters.QueueId");
    expect(hit).toBeDefined();
    expect(hit!.resource).toBe("queue:MajorIncident");
    expect(hit!.to).toBe(res(prod, "queue", "MajorIncident").arn);
    const kinds = new Set(r.replacements.map((x: any) => x.resource.split(":")[0]));
    for (const k of ["queue", "hours", "prompt", "lambda", "lexAlias", "module", "flow", "instance"]) expect(kinds.has(k)).toBe(true);
  });
});

describe("problems fail closed", () => {
  test("a resource missing from the target manifest is reported as unmapped-in-target and nothing is emitted", () => {
    const prod = env("prod");
    prod.resources = prod.resources.filter((x) => !(x.kind === "prompt" && x.name === "ClosedMessage"));
    const r = promote(devExport(), prod);
    expect(r.ok).toBe(false);
    expect(r.artifacts).toEqual([]);
    const p = r.problems.find((x: any) => x.reason === "unmapped-in-target");
    expect(p).toBeDefined();
    expect(p!.artifact).toBe("mod-after-hours");
    expect(p!.path).toBe("$.Actions[0].Parameters.PromptId");
  });
  test("a missing Lex alias in the target is reported", () => {
    const prod = env("prod");
    prod.resources = prod.resources.filter((x) => x.kind !== "lexAlias");
    const r = promote(devExport(), prod);
    expect(r.problems.some((x: any) => x.reason === "unmapped-in-target" && /lexAlias/.test(x.detail + x.value + x.path) || (x.reason === "unmapped-in-target" && x.path.includes("LexV2Bot")))).toBe(true);
  });
  test("a dev ARN that is not in the dev inventory is an unknown-reference", () => {
    const e = devExport();
    const f = e.flows.find((x) => x.ContactFlow.Name === "LFG Major Incident")!;
    const flow = JSON.parse(f.ContactFlow.Content);
    flow.Actions[0].Parameters.QueueId = `${e.inventory.instanceArn}/queue/00000000-1111-4222-8333-444455556666`;
    f.ContactFlow.Content = JSON.stringify(flow);
    const r = promote(e, env("prod"));
    expect(r.ok).toBe(false);
    expect(r.problems.map((x: any) => x.reason)).toContain("unknown-reference");
  });
  test("an unknown dev Lambda (hand-edited in the console) is reported, not passed through", () => {
    const e = devExport();
    const m = e.modules.find((x) => x.ContactFlowModule.Name === "mod-password-reset")!;
    const flow = JSON.parse(m.ContactFlowModule.Content);
    flow.Actions[0].Parameters.LambdaFunctionARN = "arn:aws:lambda:us-east-1:111122223333:function:ali-scratch-test";
    m.ContactFlowModule.Content = JSON.stringify(flow);
    const r = promote(e, env("prod"));
    expect(r.ok).toBe(false);
    expect(r.problems.some((x: any) => x.value.includes("ali-scratch-test"))).toBe(true);
  });
  test("ARNs owned by other accounts (shared services) pass through untouched", () => {
    const e = devExport();
    const f = e.flows.find((x) => x.ContactFlow.Name === "LFG Major Incident")!;
    const flow = JSON.parse(f.ContactFlow.Content);
    const shared = "arn:aws:lambda:us-east-1:999988887777:function:shared-audit";
    flow.Actions[1].Parameters.Note = shared;
    f.ContactFlow.Content = JSON.stringify(flow);
    const r = promote(e, env("prod"));
    expect(r.ok).toBe(true);
    expect(parse(art(r, "LFG Major Incident").content).Actions[1].Parameters.Note).toBe(shared);
  });
});

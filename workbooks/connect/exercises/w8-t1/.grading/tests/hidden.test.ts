// Hidden tests for connect/w8-t1 (copied to tests/__hidden__ by the grader).
import * as fs from "fs";
import * as path from "path";
import { checkRefs } from "../../pipeline/check-refs";
import { rewriteArtifact } from "../../pipeline/rewrite";
import { dev, devContent, prod, releaseArtifacts } from "../harness";

const fixture = (f: string) => JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures", f), "utf8"));
const ARN = /arn:aws[a-z-]*:[a-z0-9-]+:[a-z0-9-]*:\d{12}:[A-Za-z0-9_\-./:+=@]+/g;

describe("the deployed prod artifacts (release/prod, regenerated after the fix)", () => {
  test("every ARN in every artifact is the prod instance or a prod inventory resource", () => {
    const inv = prod();
    const known = new Set([inv.instanceArn, ...inv.resources.map((r) => r.arn)]);
    const bad: string[] = [];
    for (const a of releaseArtifacts()) {
      for (const arn of a.content.match(ARN) || []) {
        const base = arn.replace(/^(arn:aws:lambda:[^:]+:\d{12}:function:[A-Za-z0-9_-]+):[A-Za-z0-9_$-]+$/, "$1");
        if (!known.has(arn) && !known.has(base)) bad.push(`${a.name}: ${arn}`);
      }
    }
    expect(bad).toEqual([]);
  });
  test("the natural-language front door uses the prod HelpDeskBot live alias", () => {
    const inv = prod();
    const f = JSON.parse(releaseArtifacts().find((x) => x.name === "LFG Help Desk Inbound")!.content);
    const askBot = f.Actions.find((x: any) => x.Type === "ConnectParticipantWithLexBot");
    expect(askBot.Parameters.LexV2Bot.AliasArn).toBe(inv.resources.find((r) => r.kind === "lexAlias")!.arn);
  });
});

describe("rewrite (pipeline promote step)", () => {
  const expected = fixture("expected-prod.json");
  test.each([
    ["flows", "lfg-help-desk-inbound.json", "LFG Help Desk Inbound"],
    ["flows", "lfg-major-incident.json", "LFG Major Incident"],
    ["modules", "mod-after-hours.json", "mod-after-hours"],
    ["modules", "mod-password-reset.json", "mod-password-reset"],
  ])("%s/%s promotes to exactly the expected prod content", (kind, file, name) => {
    const out = JSON.parse(rewriteArtifact(devContent(kind as any, file), dev(), prod()).content);
    const exp = kind === "flows" ? expected.flows[name] : expected.modules[name];
    expect(out.Actions).toEqual(exp.Actions);
  });
  test("ARNs of any service in the dev inventory are rewritten, wherever they appear", () => {
    const d = dev();
    const lex = d.resources.find((r) => r.kind === "lexAlias")!.arn;
    const content = JSON.stringify({ Version: "2019-10-30", StartAction: "x", Actions: [
      { Identifier: "x", Type: "InvokeLambdaFunction", Parameters: { LambdaInvocationAttributes: { bot: `{"alias":"${lex}"}` } }, Transitions: {} },
    ] });
    const out = rewriteArtifact(content, d, prod()).content;
    expect(out).not.toContain("111122223333");
  });
});

describe("check-refs gate", () => {
  test("flags the dev Lex alias in the artifact that shipped in run #418, with its path", () => {
    const shipped = fixture("broken-inbound.json");
    const p = checkRefs(shipped.name, shipped.content, prod());
    expect(p).toHaveLength(1);
    expect(p[0]).toMatchObject({ path: "$.Actions[9].Parameters.LexV2Bot.AliasArn", reason: "foreign-account" });
    expect(p[0].arn).toContain(":111122223333:bot-alias/");
  });
  test("passes the fixed artifacts", () => {
    for (const a of releaseArtifacts()) expect(checkRefs(a.name, a.content, prod())).toEqual([]);
  });
  test("accepts a Lambda ARN with a qualifier when the function is in the inventory", () => {
    const inv = prod();
    const fn = inv.resources.find((r) => r.kind === "lambda")!.arn + ":live";
    const c = JSON.stringify({ Actions: [{ Parameters: { LambdaFunctionARN: fn } }] });
    expect(checkRefs("t", c, inv)).toEqual([]);
  });
  test("checks ARNs embedded in longer strings and in Metadata", () => {
    const inv = prod();
    const ghost = `${inv.instanceArn}/queue/11111111-2222-4333-8444-555555555555`;
    const c = JSON.stringify({ Metadata: { ActionMetadata: { "set-q": { queue: { id: ghost } } } }, Actions: [{ Parameters: { audit: `{"q":"${ghost}"}` } }] });
    const p = checkRefs("t", c, inv);
    expect(p.map((x) => x.path).sort()).toEqual(['$.Actions[0].Parameters.audit', '$.Metadata.ActionMetadata["set-q"].queue.id']);
  });
  test("foreign accounts are flagged unless explicitly allowed", () => {
    const inv = prod();
    const c = JSON.stringify({ Actions: [{ Parameters: { x: "arn:aws:lambda:us-east-1:999988887777:function:shared-audit" } }] });
    expect(checkRefs("t", c, inv)[0].reason).toBe("foreign-account");
    expect(checkRefs("t", c, inv, ["999988887777"])).toEqual([]);
  });
});

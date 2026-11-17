// Hidden tests for connect/w3-c2 (run from tests/__hidden__).
import { synth, byAction, sdkCalls, vcRef, dependsOnClosure, render } from "../template";

let t: any;
beforeAll(() => { t = synth(); });
const vcs = () => byAction(t, "CreateVoiceConnector");
const vcIdByRegion = (region: string) => vcs().find((c) => c.parameters.AwsRegion === region)!.logicalId;

test("one Voice Connector in us-east-1 and one in us-west-2, named and tagged", () => {
  const v = vcs();
  expect(v.map((c) => c.parameters.AwsRegion).sort()).toEqual(["us-east-1", "us-west-2"]);
  expect(v.map((c) => c.parameters.Name).sort()).toEqual(["lfg-avaya-sbce-prod-use1", "lfg-avaya-sbce-prod-usw2"]);
  for (const c of v) expect(c.parameters.Tags).toEqual(expect.arrayContaining([{ Key: "CostCenter", Value: "IT-1405" }]));
});

test("Voice Connectors take their physical id from the response and are deleted with it", () => {
  for (const c of vcs()) expect(c.physicalResourceId).toEqual({ responsePath: "VoiceConnector.VoiceConnectorId" });
  const del = byAction(t, "DeleteVoiceConnector", "Delete");
  expect(del.length).toBe(2);
  for (const d of del) expect(d.parameters.VoiceConnectorId).toBe("PHYSICAL:RESOURCEID:");
});

test("termination: public SBC /32s only, US and CA, CPS from config, one per Voice Connector", () => {
  const term = byAction(t, "PutVoiceConnectorTermination");
  expect(term.length).toBe(2);
  expect(new Set(term.map((x) => vcRef(x.parameters.VoiceConnectorId)))).toEqual(new Set([vcIdByRegion("us-east-1"), vcIdByRegion("us-west-2")]));
  for (const x of term) {
    expect(x.parameters.Termination.CidrAllowedList.sort()).toEqual(["198.51.100.10/32", "198.51.100.11/32", "203.0.113.20/32"]);
    expect(x.parameters.Termination.CallingRegions.sort()).toEqual(["CA", "US"]);
    expect(x.parameters.Termination.CpsLimit).toBe(20);
    expect(x.parameters.Termination.Disabled).toBe(false);
  }
});

test("origination: TLS over TCP 5061 to both Ashburn SBCs at priority 1 (50/50) and Dallas DR at priority 2", () => {
  const orig = byAction(t, "PutVoiceConnectorOrigination");
  expect(orig.length).toBe(2);
  for (const o of orig) {
    const routes = [...o.parameters.Origination.Routes].sort((a: any, b: any) => a.Host.localeCompare(b.Host));
    expect(routes).toEqual([
      { Host: "198.51.100.10", Port: 5061, Protocol: "TCP", Priority: 1, Weight: 50 },
      { Host: "198.51.100.11", Port: 5061, Protocol: "TCP", Priority: 1, Weight: 50 },
      { Host: "203.0.113.20", Port: 5061, Protocol: "TCP", Priority: 2, Weight: 100 },
    ]);
    expect(o.parameters.Origination.Disabled).toBe(false);
  }
});

test("configuration calls also run on update, so a config change reaches the trunk", () => {
  for (const action of ["PutVoiceConnectorTermination", "PutVoiceConnectorOrigination", "PutVoiceConnectorLoggingConfiguration"]) {
    const creates = byAction(t, action, "Create");
    const updates = byAction(t, action, "Update");
    expect(updates.length).toBe(creates.length);
    for (const c of creates) {
      const u = updates.find((x) => x.logicalId === c.logicalId)!;
      expect(u.parameters).toEqual(c.parameters);
    }
  }
});

test("a Voice Connector group puts us-east-1 at priority 1 and us-west-2 at priority 2", () => {
  const g = byAction(t, "CreateVoiceConnectorGroup");
  expect(g.length).toBe(1);
  const items = g[0].parameters.VoiceConnectorItems.map((i: any) => ({ vc: vcRef(i.VoiceConnectorId), p: i.Priority }));
  expect(items).toEqual(expect.arrayContaining([{ vc: vcIdByRegion("us-east-1"), p: 1 }, { vc: vcIdByRegion("us-west-2"), p: 2 }]));
  expect(items.length).toBe(2);
  expect(byAction(t, "DeleteVoiceConnectorGroup", "Delete").length).toBe(1);
});

test("termination credentials are never passed as an SDK-call parameter in the template", () => {
  expect(sdkCalls(t).filter((c) => c.action === "PutVoiceConnectorTerminationCredentials")).toEqual([]);
});

test("a credentials custom resource per Voice Connector reads the Secrets Manager ARN and runs after termination", () => {
  const creds = Object.entries<any>(t.Resources).filter(([, r]) => r.Type.startsWith("Custom::") && r.Type !== "Custom::AWS" && r.Properties.SecretArn);
  expect(creds.length).toBe(2);
  const terms = byAction(t, "PutVoiceConnectorTermination");
  for (const [id, r] of creds) {
    expect(r.Properties.SecretArn).toBe("arn:aws:secretsmanager:us-east-1:111122223333:secret:voice/lfg-sbce-prod/termination-AbCdEf");
    const vc = vcRef(render(r.Properties.VoiceConnectorId));
    expect(vc).toBeDefined();
    const term = terms.find((x) => vcRef(x.parameters.VoiceConnectorId) === vc)!;
    expect(dependsOnClosure(t, id).has(term.logicalId)).toBe(true);
  }
});

test("the credentials function can read only that secret", () => {
  const stmts = Object.values<any>(t.Resources)
    .filter((r) => r.Type === "AWS::IAM::Policy")
    .flatMap((r) => r.Properties.PolicyDocument.Statement)
    .filter((s: any) => [].concat(s.Action).some((a: string) => a.startsWith("secretsmanager:")));
  expect(stmts.length).toBeGreaterThan(0);
  for (const s of stmts) {
    const res = [].concat(s.Resource).map(render);
    expect(res).not.toContain("*");
    for (const r of res) expect(r).toContain("voice/lfg-sbce-prod/termination");
  }
});

test("synth refuses a private origination host", () => {
  expect(() => synth((c) => { c.origination.push({ name: "lab", host: "10.20.4.15", priority: 3, weight: 1 }); })).toThrow(/public/i);
});

test("outputs expose each Voice Connector's outbound host name for the SBC trunk config", () => {
  const outs = Object.values<any>(t.Outputs || {}).map((o) => render(o.Value));
  expect(outs.filter((v) => /VoiceConnector\.OutboundHostName/.test(v)).length).toBe(2);
});

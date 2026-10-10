// Visible tests for connect/w3-c2. The grader adds more (both Regions, routes, group, update
// behaviour, credential handling, IAM scope).
import { synth, byAction } from "./template";

let t: any;
beforeAll(() => { t = synth(); });

test("the prod config synthesizes (no private addresses in the trunk config)", () => {
  expect(t.Resources).toBeDefined();
});

test("every Voice Connector requires encryption (TLS signaling + SRTP)", () => {
  const vcs = byAction(t, "CreateVoiceConnector");
  expect(vcs.length).toBeGreaterThan(0);
  for (const c of vcs) expect(c.parameters.RequireEncryption).toBe(true);
});

test("SIP message logs and media metric logs are enabled for every Voice Connector", () => {
  const vcs = byAction(t, "CreateVoiceConnector");
  const logs = byAction(t, "PutVoiceConnectorLoggingConfiguration");
  expect(logs.length).toBe(vcs.length);
  for (const l of logs) expect(l.parameters.LoggingConfiguration).toEqual({ EnableSIPLogs: true, EnableMediaMetricLogs: true });
});

test("the termination password never appears in the synthesized template", () => {
  expect(JSON.stringify(t)).not.toContain("Avaya-SBCE-2023!");
});

test("synth refuses a private CIDR in the termination allow list", () => {
  expect(() => synth((c) => { c.termination.cidrAllowedList.push("192.168.40.0/24"); })).toThrow(/public/i);
});

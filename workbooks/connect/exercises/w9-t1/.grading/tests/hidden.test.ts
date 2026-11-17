// Hidden tests for connect/w9-t1: relay state format and guards on the rest of the SSO chain.
import * as fs from "fs";
import * as path from "path";
/* eslint-disable @typescript-eslint/no-var-requires */
const { evalOktaExpr, readUsers } = require("../../tools/saml");

const root = path.resolve(__dirname, "../..");
const j = (p: string) => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const app = j("idp/okta-connect-app.json");
const role = j("iam/role-LFG-ConnectAgents.json");
const inst = j("config/connect-instance.json");
const so = app.settings.signOn;
const attr = (suffix: string) => so.attributeStatements.find((a: any) => a.name === `https://aws.amazon.com/SAML/Attributes/${suffix}`);

describe("relay state", () => {
  const relay = String(so.defaultRelayState);
  test("is an https URL on the regional console federate endpoint (not the instance access URL)", () => {
    const u = new URL(relay);
    expect(u.protocol).toBe("https:");
    expect(u.hostname).not.toMatch(/my\.connect\.aws$|awsapps\.com$/);
    expect(u.hostname).toBe(`${inst.Region}.console.aws.amazon.com`);
  });
  test("names the production instance id, not UAT", () => {
    expect(relay).toContain(inst.Instance.Id);
    for (const o of inst.OtherInstances) expect(relay).not.toContain(o.Id);
  });
  test("a destination deep link, if present, is a URL-encoded path", () => {
    const q = relay.split("?")[1];
    if (!q) return;
    const m = /(?:^|&)destination=([^&]*)/.exec(q);
    if (!m) return;
    expect(m[1]).toMatch(/^%2F/i);
    expect(m[1]).not.toContain("/");
  });
});

describe("guards: the rest of the chain was right; keep it right", () => {
  test("ACS URL and audience are the AWS SAML endpoint values", () => {
    expect(so.ssoAcsUrl).toBe("https://signin.aws.amazon.com/saml");
    expect(so.audience).toBe("urn:amazon:webservices");
  });
  test("RoleSessionName evaluates to each agent's Connect username", () => {
    for (const u of readUsers(root)) expect(evalOktaExpr(attr("RoleSessionName").values[0], { email: u.Email, login: u.Email })).toBe(u.Username);
  });
  test("trust policy: AssumeRoleWithSAML from the provider named in the Role attribute, audience pinned", () => {
    const st = role.Role.AssumeRolePolicyDocument.Statement[0];
    expect(st.Action).toBe("sts:AssumeRoleWithSAML");
    expect(attr("Role").values[0].split(",")[1]).toBe(st.Principal.Federated);
    expect(st.Condition.StringEquals["SAML:aud"]).toBe("https://signin.aws.amazon.com/saml");
  });
  test("GetFederationToken scoped to the instance's users via ${aws:userid}", () => {
    const st = role.InlinePolicies["connect-federation"].Statement[0];
    expect(st.Action).toBe("connect:GetFederationToken");
    expect(st.Resource).toBe(`${inst.Instance.Arn}/user/\${aws:userid}`);
  });
  test("SessionDuration does not exceed the role's MaxSessionDuration (43200 s max)", () => {
    const d = Number(attr("SessionDuration").values[0]);
    expect(d).toBeGreaterThanOrEqual(900);
    expect(d).toBeLessThanOrEqual(role.Role.MaxSessionDuration);
    expect(role.Role.MaxSessionDuration).toBeLessThanOrEqual(43200);
  });
});

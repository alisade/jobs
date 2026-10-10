"use strict";
// Generates the incident bundle for connect/w9-t1 into incident/ (deterministic).
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const out = path.join(ROOT, "incident");
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
const w = (p, s) => fs.writeFileSync(path.join(out, p), s.endsWith("\n") ? s : s + "\n");
const app = JSON.parse(fs.readFileSync(path.join(ROOT, "idp/okta-connect-app.json"), "utf8"));
const INSTANCE = "5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f";
const NEW_RELAY = "https://lfg-helpdesk.my.connect.aws/ccp-v2";
const OLD_RELAY = `https://us-east-1.console.aws.amazon.com/connect/federate/${INSTANCE}?destination=%2Fccp-v2`;

w("PAGE.txt", `INC0049377  P2  Monterrey agents cannot get into the Connect agent workspace (login loop)
Opened 2026-10-08 06:22 CT by Marco Rios (Monterrey shift lead)

Since this morning every Monterrey agent who clicks the Okta tile "Amazon Connect - Help Desk"
bounces: Okta -> AWS -> a Connect page that says to sign in through your identity provider ->
back to Okta (dashboard) -> click the tile again -> same. 14 of 16 agents on shift affected, the
queue is building. Two agents who still had yesterday's Connect tab open are working.
Charlotte agents start at 08:00 ET; expect the same.

Changes in the last 24 h (from the CAB calendar, see change-records.txt):
  CHG0031177  Migrate AWS/Connect SAML apps from the legacy Okta org (lfg-legacy.okta.com) to
              lfg.okta.com (identity consolidation). Done 2026-10-07 21:00-23:00 ET by IAM team.
  CHG0031180  CISO: Okta global session policy max session lifetime 12 h -> 8 h.
              Done 2026-10-07 22:00 ET.

Thread:
[06:31] Priya (Pune, supervisor): I can log in to the AWS console with my admin tile fine.
[06:40] IAM team (Sam): the new app is a 1:1 copy, signing cert uploaded to the IAM SAML provider,
        CloudTrail shows AssumeRoleWithSAML succeeding for the agents. Must be the 8 h session
        change - Connect sessions are 12 h, maybe they now conflict?
[06:52] Jordan (Connect admin): nothing changed on the Connect side. Users exist.
Attached: har-mrios-login.txt, cloudtrail.jsonl, okta-system-log.jsonl, okta-app-legacy-export.json
`);

w("change-records.txt", `CHG0031177  Standard  Migrate AWS SAML apps to lfg.okta.com
  Implementation notes (Sam Patel, IAM):
  - Recreated "AWS Console - Admins" and "Amazon Connect - Help Desk" in lfg.okta.com from the
    vendor catalog template, copied attribute statements from the legacy org.
  - Uploaded new signing certificate to IAM SAML provider LFG-Okta (metadata replace).
  - Default relay state for the Connect app set to the Connect access URL from the
    Connect console (instance overview page).
  - Tested: admin tile lands in console OK; Connect tile authenticates (AssumeRoleWithSAML 200).
CHG0031180  Normal  Okta global session policy: max Okta session lifetime 8 hours (was 12),
  idle timeout unchanged (2 h). Applies to all users at next sign-in.
`);

w("okta-app-legacy-export.json", JSON.stringify({ ...app, _source: "lfg-legacy.okta.com export 2026-10-07 20:55 ET (before CHG0031177)", id: "0oa1legacyconn3", settings: { signOn: { ...app.settings.signOn, defaultRelayState: OLD_RELAY } } }, null, 2));

const assertion = (user, relay) => `<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" Destination="https://signin.aws.amazon.com/saml" ID="id7718" IssueInstant="2026-10-08T11:18:04.211Z" Version="2.0">
  <saml2:Issuer xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion">http://www.okta.com/exk9lfgconnect</saml2:Issuer>
  <samlp:Status><samlp:StatusCode Value="urn:oasis:names:tc:SAML:2.0:status:Success"/></samlp:Status>
  <saml2:Assertion xmlns:saml2="urn:oasis:names:tc:SAML:2.0:assertion" ID="id7719" IssueInstant="2026-10-08T11:18:04.211Z" Version="2.0">
    <saml2:Subject><saml2:NameID Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress">${user}@larkspur.example</saml2:NameID>
      <saml2:SubjectConfirmation Method="urn:oasis:names:tc:SAML:2.0:cm:bearer"><saml2:SubjectConfirmationData NotOnOrAfter="2026-10-08T11:23:04.211Z" Recipient="https://signin.aws.amazon.com/saml"/></saml2:SubjectConfirmation></saml2:Subject>
    <saml2:Conditions NotBefore="2026-10-08T11:13:04.211Z" NotOnOrAfter="2026-10-08T11:23:04.211Z"><saml2:AudienceRestriction><saml2:Audience>urn:amazon:webservices</saml2:Audience></saml2:AudienceRestriction></saml2:Conditions>
    <saml2:AuthnStatement AuthnInstant="2026-10-08T11:18:03.902Z" SessionIndex="id7719.88"><saml2:AuthnContext><saml2:AuthnContextClassRef>urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport</saml2:AuthnContextClassRef></saml2:AuthnContext></saml2:AuthnStatement>
    <saml2:AttributeStatement>
      <saml2:Attribute Name="https://aws.amazon.com/SAML/Attributes/Role"><saml2:AttributeValue>arn:aws:iam::111122223333:role/LFG-ConnectAgents,arn:aws:iam::111122223333:saml-provider/LFG-Okta</saml2:AttributeValue></saml2:Attribute>
      <saml2:Attribute Name="https://aws.amazon.com/SAML/Attributes/RoleSessionName"><saml2:AttributeValue>${user}</saml2:AttributeValue></saml2:Attribute>
      <saml2:Attribute Name="https://aws.amazon.com/SAML/Attributes/SessionDuration"><saml2:AttributeValue>43200</saml2:AttributeValue></saml2:Attribute>
    </saml2:AttributeStatement>
  </saml2:Assertion>
</samlp:Response>`;
const b64 = Buffer.from(assertion("mrios", NEW_RELAY)).toString("base64");
w("har-mrios-login.txt", `# HAR summary exported from Chrome DevTools (mrios, Monterrey, 2026-10-08 06:18 CT). Cookies redacted.
#  t(ms)  method status url                                                               -> Location
     0  GET    200  https://lfg.okta.com/app/UserHome
   412  GET    302  https://lfg.okta.com/home/amazon_aws/0oa9x2lfgconnect7/272            -> https://lfg.okta.com/app/amazon_aws/exk9lfgconnect/sso/saml
   655  GET    200  https://lfg.okta.com/app/amazon_aws/exk9lfgconnect/sso/saml           (auto-submit form to signin.aws.amazon.com/saml)
   911  POST   302  https://signin.aws.amazon.com/saml                                    -> ${NEW_RELAY}
  1240  GET    302  ${NEW_RELAY}                       -> https://lfg-helpdesk.my.connect.aws/login?redirect=%2Fccp-v2
  1502  GET    200  https://lfg-helpdesk.my.connect.aws/login?redirect=%2Fccp-v2           ("Log in through your identity provider" page)
  9877  GET    200  https://lfg.okta.com/app/UserHome                                      (agent clicks "Sign in" link -> Okta dashboard)
 12034  GET    302  https://lfg.okta.com/home/amazon_aws/0oa9x2lfgconnect7/272            -> ... (loop repeats)

# Request body of the POST https://signin.aws.amazon.com/saml (form fields)
RelayState=${encodeURIComponent(NEW_RELAY)}
SAMLResponse=${encodeURIComponent(b64)}
`);

const ct = [];
const ev = (t, name, user, extra) => ct.push(JSON.stringify({ eventVersion: "1.09", eventTime: t, eventSource: name === "AssumeRoleWithSAML" ? "sts.amazonaws.com" : "connect.amazonaws.com", eventName: name, awsRegion: "us-east-1", sourceIPAddress: user.ip, userIdentity: name === "AssumeRoleWithSAML" ? { type: "SAMLUser", principalId: `Wu5WY0qcp3x2XUC0Wr+tHkqMDSY=:${user.u}@larkspur.example`, userName: `${user.u}@larkspur.example`, identityProvider: "Wu5WY0qcp3x2XUC0Wr+tHkqMDSY=" } : { type: "AssumedRole", principalId: `AROAEXAMPLELFGAGENTS:${user.u}`, arn: `arn:aws:sts::111122223333:assumed-role/LFG-ConnectAgents/${user.u}` }, ...extra }));
const mty = { ip: "189.203.44.17" };
// yesterday (legacy org): assume + federation token
for (const [t, u] of [["2026-10-07T12:01:10Z", "mrios"], ["2026-10-07T12:03:44Z", "agarcia"], ["2026-10-07T12:04:02Z", "lvaldez"]]) {
  ev(t, "AssumeRoleWithSAML", { ...mty, u }, { requestParameters: { roleArn: "arn:aws:iam::111122223333:role/LFG-ConnectAgents", principalArn: "arn:aws:iam::111122223333:saml-provider/LFG-Okta", durationSeconds: 43200 }, responseElements: { subjectType: "persistent", audience: "https://signin.aws.amazon.com/saml", issuer: "http://www.okta.com/exk1legacyconn" } });
  ev(t.replace(/:(\d\d)Z$/, (m, s) => `:${String(Number(s) + 1).padStart(2, "0")}Z`), "GetFederationToken", { ...mty, u }, { requestParameters: { InstanceId: INSTANCE }, responseElements: null });
}
// today (new org): assume only, repeated
for (const [t, u] of [["2026-10-08T11:18:05Z", "mrios"], ["2026-10-08T11:18:17Z", "mrios"], ["2026-10-08T11:19:02Z", "agarcia"], ["2026-10-08T11:19:40Z", "mrios"], ["2026-10-08T11:20:11Z", "lvaldez"], ["2026-10-08T11:20:30Z", "agarcia"]]) {
  ev(t, "AssumeRoleWithSAML", { ...mty, u }, { requestParameters: { roleArn: "arn:aws:iam::111122223333:role/LFG-ConnectAgents", principalArn: "arn:aws:iam::111122223333:saml-provider/LFG-Okta", durationSeconds: 43200 }, responseElements: { subjectType: "persistent", audience: "https://signin.aws.amazon.com/saml", issuer: "http://www.okta.com/exk9lfgconnect" } });
}
ev("2026-10-08T11:31:52Z", "AssumeRoleWithSAML", { ip: "49.36.112.9", u: "pnatarajan" }, { requestParameters: { roleArn: "arn:aws:iam::111122223333:role/LFG-ConsoleAdmins", principalArn: "arn:aws:iam::111122223333:saml-provider/LFG-Okta", durationSeconds: 3600 }, responseElements: { subjectType: "persistent", audience: "https://signin.aws.amazon.com/saml", issuer: "http://www.okta.com/exk9lfgconsole" } });
w("cloudtrail.jsonl", ct.join("\n"));

w("okta-system-log.jsonl", [
  { published: "2026-10-08T02:01:44Z", eventType: "policy.lifecycle.update", displayMessage: "Update policy", target: [{ displayName: "Global Session Policy - Default", detailEntry: { maxSessionLifetimeMinutes: 480 } }], outcome: { result: "SUCCESS" } },
  { published: "2026-10-08T11:18:03Z", eventType: "user.session.start", actor: { alternateId: "mrios@larkspur.example" }, outcome: { result: "SUCCESS" } },
  { published: "2026-10-08T11:18:04Z", eventType: "user.authentication.sso", actor: { alternateId: "mrios@larkspur.example" }, target: [{ displayName: "Amazon Connect - Help Desk" }], outcome: { result: "SUCCESS" } },
  { published: "2026-10-08T11:18:16Z", eventType: "user.authentication.sso", actor: { alternateId: "mrios@larkspur.example" }, target: [{ displayName: "Amazon Connect - Help Desk" }], outcome: { result: "SUCCESS" } },
  { published: "2026-10-08T11:19:39Z", eventType: "user.authentication.sso", actor: { alternateId: "mrios@larkspur.example" }, target: [{ displayName: "Amazon Connect - Help Desk" }], outcome: { result: "SUCCESS" } },
  { published: "2026-10-08T11:31:51Z", eventType: "user.authentication.sso", actor: { alternateId: "pnatarajan@larkspur.example" }, target: [{ displayName: "AWS Console - Admins" }], outcome: { result: "SUCCESS" } },
].map((x) => JSON.stringify(x)).join("\n"));
console.log("incident bundle written to incident/");

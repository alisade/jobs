// Visible tests for connect/w9-t1. The grader adds more checks of the IdP and IAM configuration.
import * as fs from "fs";
import * as path from "path";

const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
const app = JSON.parse(fs.readFileSync(path.join(root, "idp/okta-connect-app.json"), "utf8"));
const inst = JSON.parse(fs.readFileSync(path.join(root, "config/connect-instance.json"), "utf8"));

test("default relay state federates into the production help desk instance", () => {
  const u = new URL(app.settings.signOn.defaultRelayState);
  expect(`${u.origin}${u.pathname}`).toBe(`https://${inst.Region}.console.aws.amazon.com/connect/federate/${inst.Instance.Id}`);
});

test("the Role attribute still pairs the agents role with the Okta SAML provider", () => {
  const role = app.settings.signOn.attributeStatements.find((a: any) => a.name.endsWith("/Role"));
  expect(role.values[0]).toBe("arn:aws:iam::111122223333:role/LFG-ConnectAgents,arn:aws:iam::111122223333:saml-provider/LFG-Okta");
});

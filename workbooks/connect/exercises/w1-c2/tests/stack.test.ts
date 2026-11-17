// Visible tests for connect/w1-c2. The grader adds more.
import { Match } from "aws-cdk-lib/assertions";
import { synth } from "./synth";

test("one SAML instance with flow logs and Contact Lens enabled", () => {
  const { template } = synth("dev");
  template.resourceCountIs("AWS::Connect::Instance", 1);
  template.hasResourceProperties("AWS::Connect::Instance", {
    IdentityManagementType: "SAML",
    InstanceAlias: "lfg-helpdesk-dev",
    Attributes: Match.objectLike({ InboundCalls: true, OutboundCalls: true, ContactflowLogs: true, ContactLens: true }),
  });
});

test("staffed hours are Mon-Fri 06:00-20:00 Eastern", () => {
  const { template } = synth("dev");
  template.hasResourceProperties("AWS::Connect::HoursOfOperation", {
    Name: "HelpDeskHours",
    TimeZone: "America/New_York",
    Config: Match.arrayWith([{ Day: "MONDAY", StartTime: { Hours: 6, Minutes: 0 }, EndTime: { Hours: 20, Minutes: 0 } }]),
  });
});

test("every queue in the config exists", () => {
  const { template } = synth("dev");
  template.resourceCountIs("AWS::Connect::Queue", 4);
  template.hasResourceProperties("AWS::Connect::Queue", { Name: "MajorIncident", MaxContacts: 100 });
});

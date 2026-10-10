// Hidden tests for connect/w1-c2.
import { Match } from "aws-cdk-lib/assertions";
import { synth } from "../synth";

const res = (t: any, type: string) => Object.entries<any>(t.toJSON().Resources).filter(([, r]) => r.Type === type);

describe("hours and holidays", () => {
  test("MajorIncident queue uses 24x7 hours, others the staffed hours", () => {
    const { template } = synth("dev");
    const t = template.toJSON().Resources;
    const hoursId = (name: string) => Object.keys(t).find((k) => t[k].Type === "AWS::Connect::HoursOfOperation" && t[k].Properties.Name === name);
    const queue = (name: string) => Object.values<any>(t).find((r) => r.Type === "AWS::Connect::Queue" && r.Properties.Name === name);
    expect(JSON.stringify(queue("MajorIncident").Properties.HoursOfOperationArn)).toContain(hoursId("Always"));
    expect(JSON.stringify(queue("GeneralSupport").Properties.HoursOfOperationArn)).toContain(hoursId("HelpDeskHours"));
  });
  test("24x7 hours cover all seven days", () => {
    const { template } = synth("dev");
    const always = res(template, "AWS::Connect::HoursOfOperation").find(([, r]) => r.Properties.Name === "Always")![1];
    expect(always.Properties.Config.map((c: any) => c.Day).sort()).toEqual(["FRIDAY", "MONDAY", "SATURDAY", "SUNDAY", "THURSDAY", "TUESDAY", "WEDNESDAY"]);
    expect(always.Properties.TimeZone).toBe("America/New_York");
  });
  test("holidays are CLOSED overrides on the staffed hours, one per configured date", () => {
    const { template } = synth("dev");
    const staffed = res(template, "AWS::Connect::HoursOfOperation").find(([, r]) => r.Properties.Name === "HelpDeskHours")![1];
    const ov = staffed.Properties.HoursOfOperationOverrides;
    expect(ov).toHaveLength(4);
    for (const o of ov) {
      expect(o.OverrideType).toBe("CLOSED");
      expect(o.EffectiveFrom).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(o.EffectiveTill).toBe(o.EffectiveFrom);
      expect(o.OverrideConfig.length).toBeGreaterThan(0);
    }
    expect(ov.map((o: any) => o.EffectiveFrom)).toContain("2026-12-25");
  });
  test("the 24x7 hours carry no holiday closures (outages do not take holidays)", () => {
    const { template } = synth("dev");
    const always = res(template, "AWS::Connect::HoursOfOperation").find(([, r]) => r.Properties.Name === "Always")![1];
    expect(always.Properties.HoursOfOperationOverrides || []).toHaveLength(0);
  });
  test("a holiday added to the config appears without code changes", () => {
    const { template } = synth("dev", (c) => c.holidays.push({ name: "Juneteenth 2027", date: "2027-06-18" }));
    const staffed = res(template, "AWS::Connect::HoursOfOperation").find(([, r]) => r.Properties.Name === "HelpDeskHours")![1];
    expect(staffed.Properties.HoursOfOperationOverrides).toHaveLength(5);
  });
});

describe("routing profiles", () => {
  test("two routing profiles with voice 1 and chat concurrency from config", () => {
    const { template } = synth("dev");
    template.resourceCountIs("AWS::Connect::RoutingProfile", 2);
    template.hasResourceProperties("AWS::Connect::RoutingProfile", {
      Name: "Tier1",
      MediaConcurrencies: Match.arrayWith([Match.objectLike({ Channel: "VOICE", Concurrency: 1 }), Match.objectLike({ Channel: "CHAT", Concurrency: 3 })]),
    });
  });
  test("queue configs carry priority and delay for both voice and chat", () => {
    const { template } = synth("dev");
    const vip = res(template, "AWS::Connect::RoutingProfile").find(([, r]) => r.Properties.Name === "VIPAnalyst")![1];
    const qc = vip.Properties.QueueConfigs;
    expect(qc).toHaveLength(6);
    const delayed = qc.filter((c: any) => c.Delay === 30);
    expect(delayed).toHaveLength(2);
    expect(delayed.map((c: any) => c.QueueReference.Channel).sort()).toEqual(["CHAT", "VOICE"]);
    expect(delayed.every((c: any) => c.Priority === 3)).toBe(true);
  });
  test("queue references are tokens to the queues in this stack, never literal ARNs", () => {
    const { template } = synth("dev");
    for (const [, rp] of res(template, "AWS::Connect::RoutingProfile")) {
      for (const c of rp.Properties.QueueConfigs) expect(typeof c.QueueReference.QueueArn).toBe("object");
      expect(typeof rp.Properties.DefaultOutboundQueueArn).toBe("object");
    }
  });
  test("an unknown queue in a routing profile fails synth with a clear message", () => {
    expect(() => synth("dev", (c) => c.routingProfiles.Tier1.queues.push({ queue: "Typo", priority: 1, delay: 0 }))).toThrow(/Typo/);
  });
});

describe("Lex and Lambda integrations", () => {
  test("Lex V2 bot with en_US locale, configured threshold, intents and a fallback intent", () => {
    const { template } = synth("dev");
    template.hasResourceProperties("AWS::Lex::Bot", {
      BotLocales: [Match.objectLike({
        LocaleId: "en_US",
        NluConfidenceThreshold: 0.4,
        Intents: Match.arrayWith([
          Match.objectLike({ Name: "ResetPassword", SampleUtterances: Match.arrayWith([{ Utterance: "I forgot my password" }]) }),
          Match.objectLike({ Name: "FallbackIntent", ParentIntentSignature: "AMAZON.FallbackIntent" }),
        ]),
      })],
    });
  });
  test("bot name is environment-specific", () => {
    synth("prod").template.hasResourceProperties("AWS::Lex::Bot", { Name: "lfg-helpdesk-bot-prod" });
  });
  test("a numbered bot version and a 'live' alias pointing at it (Connect must not use DRAFT/TestBotAlias)", () => {
    const { template } = synth("dev");
    template.resourceCountIs("AWS::Lex::BotVersion", 1);
    const alias = res(template, "AWS::Lex::BotAlias")[0][1];
    expect(alias.Properties.BotAliasName).toBe("live");
    expect(JSON.stringify(alias.Properties.BotVersion)).toMatch(/BotVersion/);
  });
  test("Connect is associated with the bot alias ARN", () => {
    const { template } = synth("dev");
    const lexAssoc = res(template, "AWS::Connect::IntegrationAssociation").filter(([, r]) => r.Properties.IntegrationType === "LEX_BOT");
    expect(lexAssoc).toHaveLength(1);
    expect(JSON.stringify(lexAssoc[0][1].Properties.IntegrationArn)).toMatch(/BotAlias.*Arn/);
  });
  test("both Lambdas are associated with the instance", () => {
    const { template } = synth("dev");
    const l = res(template, "AWS::Connect::IntegrationAssociation").filter(([, r]) => r.Properties.IntegrationType === "LAMBDA_FUNCTION");
    expect(l).toHaveLength(2);
    expect(JSON.stringify(l)).toContain("lfg-identify-caller");
    expect(JSON.stringify(l)).toContain("lfg-password-reset");
  });
});

describe("contact flow", () => {
  const flowRes = (template: any) => res(template, "AWS::Connect::ContactFlow")[0][1];
  test("one ACTIVE CONTACT_FLOW", () => {
    const { template } = synth("dev");
    template.resourceCountIs("AWS::Connect::ContactFlow", 1);
    template.hasResourceProperties("AWS::Connect::ContactFlow", { Type: "CONTACT_FLOW", State: "ACTIVE" });
  });
  test("content is built with Fn::Sub from the template and maps every placeholder", () => {
    const { template } = synth("dev");
    const content = flowRes(template).Properties.Content;
    expect(content["Fn::Sub"]).toBeDefined();
    const [body, vars] = content["Fn::Sub"];
    const names = (body.match(/\$\{([A-Za-z0-9]+)\}/g) || []).map((m: string) => m.slice(2, -1));
    expect(names.length).toBeGreaterThanOrEqual(5);
    for (const n of names) expect(vars).toHaveProperty(n);
  });
  test("queue placeholders resolve to the queues of this stack (GetAtt), not literals", () => {
    const { template } = synth("dev");
    const vars = flowRes(template).Properties.Content["Fn::Sub"][1];
    expect(vars.QueueGeneralSupport).toEqual({ "Fn::GetAtt": [expect.stringMatching(/QueueGeneralSupport/), "QueueArn"] });
    expect(vars.HoursHelpDeskHours["Fn::GetAtt"][1]).toBe("HoursOfOperationArn");
  });
  test("no account-specific ARN is baked into the flow body", () => {
    for (const env of ["dev", "prod"] as const) {
      const { template } = synth(env);
      const body = flowRes(template).Properties.Content["Fn::Sub"][0];
      expect(body).not.toMatch(/arn:aws:/);
      expect(body).not.toMatch(/111122223333|444455556666/);
      expect(() => JSON.parse(body)).not.toThrow();
    }
  });
  test("a placeholder with no matching resource fails synth (not deploy)", () => {
    const { flowTemplate } = require("../../lib/helpdesk-stack").loadConfig(require("../synth").root);
    expect(() => synth("dev", undefined, flowTemplate.replace("${QueueVIPDesk}", "${QueueVipDesk}"))).toThrow(/QueueVipDesk/);
  });
});

describe("environments", () => {
  test("prod retains the instance; dev does not", () => {
    const prod = res(synth("prod").template, "AWS::Connect::Instance")[0][1];
    const dev = res(synth("dev").template, "AWS::Connect::Instance")[0][1];
    expect(prod.DeletionPolicy).toBe("Retain");
    expect(dev.DeletionPolicy).not.toBe("Retain");
  });
  test("instance is tagged with environment and cost center", () => {
    synth("prod").template.hasResourceProperties("AWS::Connect::Instance", {
      InstanceAlias: "lfg-helpdesk-prod",
      Tags: Match.arrayWith([{ Key: "CostCenter", Value: "IT-0420" }, { Key: "Environment", Value: "prod" }]),
    });
  });
  test("an unknown environment fails fast", () => {
    expect(() => synth("qa" as any)).toThrow(/qa/);
  });
});

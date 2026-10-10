import * as fs from "fs";
import * as path from "path";
import { Stack, StackProps, Fn, Tags, RemovalPolicy, CfnOutput } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as connect from "aws-cdk-lib/aws-connect";
import * as lex from "aws-cdk-lib/aws-lex";
import * as iam from "aws-cdk-lib/aws-iam";

export type EnvName = "dev" | "prod";

export interface HelpDeskStackProps extends StackProps {
  envName: EnvName;
  /** Parsed config/helpdesk.json (tests pass variants of it). */
  config: any;
  /** Flow template text; ${Name} placeholders are resolved per environment. */
  flowTemplate: string;
}

const DAYS = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"];

function hm(s: string) {
  const [h, m] = s.split(":").map(Number);
  return { hours: h, minutes: m };
}

export function loadConfig(root = path.resolve(__dirname, "..")) {
  return {
    config: JSON.parse(fs.readFileSync(path.join(root, "config/helpdesk.json"), "utf8")),
    flowTemplate: fs.readFileSync(path.join(root, "flows/helpdesk-inbound.template.json"), "utf8"),
  };
}

export class HelpDeskStack extends Stack {
  public readonly instance: connect.CfnInstance;
  public readonly queues: Record<string, connect.CfnQueue> = {};

  constructor(scope: Construct, id: string, props: HelpDeskStackProps) {
    super(scope, id, props);
    const { config: cfg, envName } = props;
    const envCfg = cfg.envs[envName];
    if (!envCfg) throw new Error(`unknown envName ${envName}; expected one of ${Object.keys(cfg.envs).join(", ")}`);

    // 1. Instance: SAML identity, logging and analytics on, retained in prod.
    this.instance = new connect.CfnInstance(this, "Instance", {
      identityManagementType: "SAML",
      instanceAlias: envCfg.instanceAlias,
      attributes: {
        inboundCalls: true,
        outboundCalls: true,
        contactflowLogs: true,
        contactLens: true,
        earlyMedia: true,
        autoResolveBestVoices: true,
      },
    });
    this.instance.applyRemovalPolicy(envCfg.retain ? RemovalPolicy.RETAIN : RemovalPolicy.DESTROY);
    for (const [k, v] of Object.entries<string>(cfg.tags)) Tags.of(this).add(k, v);
    Tags.of(this).add("Environment", envName);
    const instanceArn = this.instance.attrArn;

    // 2. Hours, with holiday closures as CLOSED overrides on the staffed hours only.
    const hours: Record<string, connect.CfnHoursOfOperation> = {};
    for (const [name, h] of Object.entries<any>(cfg.hours)) {
      const isStaffed = name === "HelpDeskHours";
      hours[name] = new connect.CfnHoursOfOperation(this, `Hours${name}`, {
        instanceArn,
        name,
        description: h.description,
        timeZone: cfg.timeZone,
        config: h.days.map((day: string) => ({ day, startTime: hm(h.start), endTime: hm(h.end) })),
        hoursOfOperationOverrides: isStaffed
          ? cfg.holidays.map((hol: any) => ({
              overrideName: hol.name,
              overrideType: "CLOSED",
              effectiveFrom: hol.date,
              effectiveTill: hol.date,
              overrideConfig: [{ day: DAYS[(new Date(`${hol.date}T12:00:00Z`).getUTCDay() + 6) % 7], startTime: { hours: 0, minutes: 0 }, endTime: { hours: 23, minutes: 59 } }],
            }))
          : undefined,
      });
    }

    // 3. Queues.
    for (const [name, q] of Object.entries<any>(cfg.queues)) {
      if (!hours[q.hours]) throw new Error(`queue ${name} references unknown hours ${q.hours}`);
      this.queues[name] = new connect.CfnQueue(this, `Queue${name}`, {
        instanceArn,
        name,
        description: q.description,
        hoursOfOperationArn: hours[q.hours].attrHoursOfOperationArn,
        maxContacts: q.maxContacts,
      });
    }

    // 4. Routing profiles: voice + chat concurrency, priority/delay per queue and channel.
    for (const [name, rp] of Object.entries<any>(cfg.routingProfiles)) {
      const queueConfigs: connect.CfnRoutingProfile.RoutingProfileQueueConfigProperty[] = [];
      for (const qc of rp.queues) {
        const q = this.queues[qc.queue];
        if (!q) throw new Error(`routing profile ${name} references unknown queue ${qc.queue}`);
        for (const channel of ["VOICE", "CHAT"]) {
          queueConfigs.push({ priority: qc.priority, delay: qc.delay, queueReference: { channel, queueArn: q.attrQueueArn } });
        }
      }
      new connect.CfnRoutingProfile(this, `RoutingProfile${name}`, {
        instanceArn,
        name,
        description: rp.description,
        defaultOutboundQueueArn: this.queues.GeneralSupport.attrQueueArn,
        mediaConcurrencies: [
          { channel: "VOICE", concurrency: rp.voice, crossChannelBehavior: { behaviorType: "ROUTE_CURRENT_CHANNEL_ONLY" } },
          { channel: "CHAT", concurrency: rp.chat, crossChannelBehavior: { behaviorType: "ROUTE_CURRENT_CHANNEL_ONLY" } },
        ],
        queueConfigs,
      });
    }

    // 5. Lambda integrations (functions are owned by the integrations team; referenced by name).
    const lambdaArns: Record<string, string> = {};
    for (const [key, fnName] of Object.entries<string>(cfg.lambdas)) {
      lambdaArns[key] = Fn.sub(`arn:\${AWS::Partition}:lambda:\${AWS::Region}:\${AWS::AccountId}:function:${fnName}`);
      new connect.CfnIntegrationAssociation(this, `Lambda${key}`, {
        instanceId: instanceArn,
        integrationType: "LAMBDA_FUNCTION",
        integrationArn: lambdaArns[key],
      });
    }

    // 6. Lex V2 bot: locale, intents (plus the required fallback), version, alias, Connect association.
    const lexRole = new iam.Role(this, "LexRole", { assumedBy: new iam.ServicePrincipal("lexv2.amazonaws.com") });
    const bot = new lex.CfnBot(this, "HelpDeskBot", {
      name: `${cfg.lex.botName}-${envName}`,
      roleArn: lexRole.roleArn,
      dataPrivacy: { ChildDirected: false },
      idleSessionTtlInSeconds: 300,
      autoBuildBotLocales: true,
      botLocales: [
        {
          localeId: cfg.lex.localeId,
          nluConfidenceThreshold: cfg.lex.nluConfidenceThreshold,
          intents: [
            ...Object.entries<string[]>(cfg.lex.intents).map(([intent, utterances]) => ({
              name: intent,
              sampleUtterances: utterances.map((utterance) => ({ utterance })),
            })),
            { name: "FallbackIntent", parentIntentSignature: "AMAZON.FallbackIntent" },
          ],
        },
      ],
    });
    const version = new lex.CfnBotVersion(this, "HelpDeskBotVersion", {
      botId: bot.attrId,
      botVersionLocaleSpecification: [{ localeId: cfg.lex.localeId, botVersionLocaleDetails: { sourceBotVersion: "DRAFT" } }],
    });
    const alias = new lex.CfnBotAlias(this, "HelpDeskBotAlias", {
      botId: bot.attrId,
      botAliasName: cfg.lex.aliasName,
      botVersion: version.attrBotVersion,
      botAliasLocaleSettings: [{ localeId: cfg.lex.localeId, botAliasLocaleSetting: { enabled: true } }],
    });
    new connect.CfnIntegrationAssociation(this, "LexAssociation", {
      instanceId: instanceArn,
      integrationType: "LEX_BOT",
      integrationArn: alias.attrArn,
    });

    // 7. Inbound flow: template placeholders resolved to this environment's resources by Fn::Sub.
    const vars: Record<string, string> = {
      HoursHelpDeskHours: hours.HelpDeskHours.attrHoursOfOperationArn,
      LambdaIdentifyCaller: lambdaArns.IdentifyCaller,
      LambdaPasswordReset: lambdaArns.PasswordReset,
    };
    for (const [name, q] of Object.entries(this.queues)) vars[`Queue${name}`] = q.attrQueueArn;
    const wanted = new Set((props.flowTemplate.match(/\$\{([A-Za-z0-9]+)\}/g) || []).map((m) => m.slice(2, -1)));
    const missing = [...wanted].filter((w) => !(w in vars));
    if (missing.length) throw new Error(`flow template references unknown placeholders: ${missing.join(", ")}`);
    JSON.parse(props.flowTemplate); // fail synth on malformed JSON, not at deploy
    const flow = new connect.CfnContactFlow(this, "InboundFlow", {
      instanceArn,
      name: "LFG Help Desk Inbound",
      type: "CONTACT_FLOW",
      state: "ACTIVE",
      description: "Main inbound flow for the IT help desk",
      content: Fn.sub(props.flowTemplate, Object.fromEntries([...wanted].map((w) => [w, vars[w]]))),
    });

    new CfnOutput(this, "InstanceArn", { value: instanceArn });
    new CfnOutput(this, "InboundFlowArn", { value: flow.attrContactFlowArn });
  }
}

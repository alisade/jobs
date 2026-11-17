import * as fs from "fs";
import * as path from "path";
import { Stack, StackProps, Fn, Tags, CfnOutput } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as connect from "aws-cdk-lib/aws-connect";
// import * as lex from "aws-cdk-lib/aws-lex";
// import * as iam from "aws-cdk-lib/aws-iam";

export type EnvName = "dev" | "prod";

export interface HelpDeskStackProps extends StackProps {
  envName: EnvName;
  /** Parsed config/helpdesk.json (tests pass variants of it). */
  config: any;
  /** Flow template text; ${Name} placeholders are resolved per environment. */
  flowTemplate: string;
}

export function loadConfig(root = path.resolve(__dirname, "..")) {
  return {
    config: JSON.parse(fs.readFileSync(path.join(root, "config/helpdesk.json"), "utf8")),
    flowTemplate: fs.readFileSync(path.join(root, "flows/helpdesk-inbound.template.json"), "utf8"),
  };
}

// The pilot stack, written by hand against the dev account. Make it config-driven and
// environment-safe; see README.md for the requirements.
export class HelpDeskStack extends Stack {
  public readonly instance: connect.CfnInstance;
  public readonly queues: Record<string, connect.CfnQueue> = {};

  constructor(scope: Construct, id: string, props: HelpDeskStackProps) {
    super(scope, id, props);
    const { config: cfg, envName } = props;
    const envCfg = cfg.envs[envName] || cfg.envs.dev;

    this.instance = new connect.CfnInstance(this, "Instance", {
      identityManagementType: "SAML",
      instanceAlias: envCfg.instanceAlias,
      attributes: { inboundCalls: true, outboundCalls: true },
      // TODO: flow logs, Contact Lens (conversational analytics), early media; retain in prod; tags
    });
    const instanceArn = this.instance.attrArn;

    // TODO: time zone, the 24x7 hours, holiday closures from config.holidays
    const helpDeskHours = new connect.CfnHoursOfOperation(this, "HoursHelpDeskHours", {
      instanceArn,
      name: "HelpDeskHours",
      timeZone: "UTC",
      config: ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"].map((day) => ({
        day,
        startTime: { hours: 6, minutes: 0 },
        endTime: { hours: 20, minutes: 0 },
      })),
    });

    for (const [name, q] of Object.entries<any>(cfg.queues)) {
      this.queues[name] = new connect.CfnQueue(this, `Queue${name}`, {
        instanceArn,
        name,
        description: q.description,
        hoursOfOperationArn: helpDeskHours.attrHoursOfOperationArn, // TODO: per-queue hours
        maxContacts: q.maxContacts,
      });
    }

    // TODO: routing profiles from config.routingProfiles (media concurrency, priority/delay per channel)
    // TODO: Lambda integrations, Lex V2 bot + version + alias + Connect association

    // The contractor pasted dev ARNs into the template at deploy time. This only works in dev.
    const devPrefix = "arn:aws:connect:us-east-1:111122223333:instance/5f0c4a7e-1b2d-4c3e-9f10-2a3b4c5d6e7f";
    const content = props.flowTemplate
      .replace(/\$\{Queue([A-Za-z]+)\}/g, (_m, q) => `${devPrefix}/queue/q-${q.toLowerCase()}`)
      .replace("${HoursHelpDeskHours}", `${devPrefix}/operating-hours/hoo-helpdesk`)
      .replace(/\$\{Lambda([A-Za-z]+)\}/g, (_m, l) => `arn:aws:lambda:us-east-1:111122223333:function:${l}`);
    const flow = new connect.CfnContactFlow(this, "InboundFlow", {
      instanceArn,
      name: "LFG Help Desk Inbound",
      type: "CONTACT_FLOW",
      content,
    });

    new CfnOutput(this, "InstanceArn", { value: instanceArn });
    new CfnOutput(this, "InboundFlowArn", { value: flow.attrContactFlowArn });
    void Fn;
    void Tags;
  }
}

// LFG SIP trunk for the Avaya SBCE during coexistence: Amazon Chime SDK Voice Connectors in two
// Regions behind a Voice Connector group. CloudFormation has no resource types for Chime SDK
// Voice, so every piece is an SDK call made by a custom resource (AwsCustomResource for plain
// calls, a small provider Lambda for the termination credentials so the password never lands in
// the template).
import * as fs from "fs";
import * as path from "path";
import { CfnOutput, CustomResource, Duration, Stack, StackProps, Tags } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cr from "aws-cdk-lib/custom-resources";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";

export interface EnvConfig {
  account: string;
  region: string;
  namePrefix: string;
  voiceConnectors: { key: string; awsRegion: "us-east-1" | "us-west-2"; groupPriority: number }[];
  termination: { cidrAllowedList: string[]; callingRegions: string[]; cpsLimit: number };
  origination: { name: string; host: string; priority: number; weight: number }[];
  terminationCredentials: { username: string; secretArn: string; legacyPassword?: string };
  tags: Record<string, string>;
}

export function loadEnvironment(name: string, file = path.join(__dirname, "../config/environments.json")): EnvConfig {
  const all = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!all[name]) throw new Error(`Unknown env "${name}". Available: ${Object.keys(all).join(", ")}`);
  return all[name];
}

/** True for RFC 1918, CGNAT (RFC 6598), loopback and link-local IPv4 space. */
export function isPrivateIpv4(cidrOrIp: string): boolean {
  const [a, b] = cidrOrIp.split("/")[0].split(".").map(Number);
  return a === 10 || a === 127 || (a === 172 && b >= 16 && b <= 31) || (a === 192 && b === 168) || (a === 100 && b >= 64 && b <= 127) || (a === 169 && b === 254);
}

function assertPublic(values: string[], what: string): void {
  const bad = values.filter(isPrivateIpv4);
  if (bad.length) {
    throw new Error(`${what} must be publicly routable (Voice Connector only reaches public addresses); remove ${bad.join(", ")}`);
  }
}

const SDK = "ChimeSDKVoice";
const policy = cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE });

class TrunkVoiceConnector extends Construct {
  readonly voiceConnectorId: string;
  readonly outboundHostName: string;
  readonly termination: cr.AwsCustomResource;

  constructor(scope: Construct, id: string, props: { cfg: EnvConfig; key: string; awsRegion: string }) {
    super(scope, id);
    const { cfg } = props;
    const vc = new cr.AwsCustomResource(this, "VoiceConnector", {
      onCreate: {
        service: SDK,
        action: "CreateVoiceConnector",
        parameters: {
          Name: `${cfg.namePrefix}-${props.key}`,
          AwsRegion: props.awsRegion,
          RequireEncryption: true,
          Tags: Object.entries(cfg.tags).map(([Key, Value]) => ({ Key, Value })),
        },
        physicalResourceId: cr.PhysicalResourceId.fromResponse("VoiceConnector.VoiceConnectorId"),
      },
      onDelete: { service: SDK, action: "DeleteVoiceConnector", parameters: { VoiceConnectorId: new cr.PhysicalResourceIdReference() } },
      policy,
      installLatestAwsSdk: false,
    });
    this.voiceConnectorId = vc.getResponseField("VoiceConnector.VoiceConnectorId");
    this.outboundHostName = vc.getResponseField("VoiceConnector.OutboundHostName");

    const put = (name: string, action: string, parameters: Record<string, unknown>) => {
      const call: cr.AwsSdkCall = { service: SDK, action, parameters, physicalResourceId: cr.PhysicalResourceId.of(`${cfg.namePrefix}-${props.key}-${name}`) };
      const r = new cr.AwsCustomResource(this, name, { onCreate: call, onUpdate: call, policy, installLatestAwsSdk: false });
      r.node.addDependency(vc);
      return r;
    };

    this.termination = put("Termination", "PutVoiceConnectorTermination", {
      VoiceConnectorId: this.voiceConnectorId,
      Termination: {
        CidrAllowedList: cfg.termination.cidrAllowedList,
        CallingRegions: cfg.termination.callingRegions,
        CpsLimit: cfg.termination.cpsLimit,
        Disabled: false,
      },
    });
    put("Origination", "PutVoiceConnectorOrigination", {
      VoiceConnectorId: this.voiceConnectorId,
      Origination: {
        Disabled: false,
        Routes: cfg.origination.map((o) => ({ Host: o.host, Port: 5061, Protocol: "TCP", Priority: o.priority, Weight: o.weight })),
      },
    });
    put("Logging", "PutVoiceConnectorLoggingConfiguration", {
      VoiceConnectorId: this.voiceConnectorId,
      LoggingConfiguration: { EnableSIPLogs: true, EnableMediaMetricLogs: true },
    });
  }
}

const CREDENTIALS_HANDLER = [
  'const { SecretsManagerClient, GetSecretValueCommand } = require("@aws-sdk/client-secrets-manager");',
  'const { ChimeSDKVoiceClient, PutVoiceConnectorTerminationCredentialsCommand, DeleteVoiceConnectorTerminationCredentialsCommand } = require("@aws-sdk/client-chime-sdk-voice");',
  "exports.handler = async (event) => {",
  "  const p = event.ResourceProperties;",
  "  const voice = new ChimeSDKVoiceClient({});",
  '  if (event.RequestType === "Delete") {',
  "    await voice.send(new DeleteVoiceConnectorTerminationCredentialsCommand({ VoiceConnectorId: p.VoiceConnectorId, Usernames: [p.Username] })).catch(() => undefined);",
  "    return { PhysicalResourceId: event.PhysicalResourceId };",
  "  }",
  "  const sm = new SecretsManagerClient({});",
  "  const secret = await sm.send(new GetSecretValueCommand({ SecretId: p.SecretArn }));",
  "  const password = JSON.parse(secret.SecretString).password;",
  "  await voice.send(new PutVoiceConnectorTerminationCredentialsCommand({ VoiceConnectorId: p.VoiceConnectorId, Credentials: [{ Username: p.Username, Password: password }] }));",
  '  return { PhysicalResourceId: p.VoiceConnectorId + "/" + p.Username };',
  "};",
].join("\n");

export class VoiceConnectorStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & { cfg: EnvConfig }) {
    super(scope, id, props);
    const { cfg } = props;
    assertPublic(cfg.termination.cidrAllowedList, "termination.cidrAllowedList");
    assertPublic(cfg.origination.map((o) => o.host), "origination hosts");
    Object.entries(cfg.tags).forEach(([k, v]) => Tags.of(this).add(k, v));

    const secret = secretsmanager.Secret.fromSecretCompleteArn(this, "TerminationSecret", cfg.terminationCredentials.secretArn);
    const fn = new lambda.Function(this, "TerminationCredentialsFn", {
      runtime: lambda.Runtime.NODEJS_22_X,
      handler: "index.handler",
      code: lambda.Code.fromInline(CREDENTIALS_HANDLER),
      timeout: Duration.seconds(30),
      description: "Sets Voice Connector termination credentials from Secrets Manager",
    });
    secret.grantRead(fn);
    fn.addToRolePolicy(new iam.PolicyStatement({
      actions: ["chime:PutVoiceConnectorTerminationCredentials", "chime:DeleteVoiceConnectorTerminationCredentials"],
      resources: ["*"],
    }));
    const provider = new cr.Provider(this, "TerminationCredentialsProvider", { onEventHandler: fn });

    const vcs = cfg.voiceConnectors.map((v) => ({ v, trunk: new TrunkVoiceConnector(this, `Vc-${v.key}`, { cfg, key: v.key, awsRegion: v.awsRegion }) }));
    for (const { v, trunk } of vcs) {
      const creds = new CustomResource(this, `TerminationCredentials-${v.key}`, {
        serviceToken: provider.serviceToken,
        resourceType: "Custom::VoiceConnectorTerminationCredentials",
        properties: { VoiceConnectorId: trunk.voiceConnectorId, Username: cfg.terminationCredentials.username, SecretArn: secret.secretArn },
      });
      creds.node.addDependency(trunk.termination);
      new CfnOutput(this, `VoiceConnectorId-${v.key}`, { value: trunk.voiceConnectorId });
      new CfnOutput(this, `OutboundHostName-${v.key}`, { value: trunk.outboundHostName });
    }

    const items = vcs.map(({ v, trunk }) => ({ VoiceConnectorId: trunk.voiceConnectorId, Priority: v.groupPriority }));
    const group = new cr.AwsCustomResource(this, "VoiceConnectorGroup", {
      onCreate: {
        service: SDK,
        action: "CreateVoiceConnectorGroup",
        parameters: { Name: `${cfg.namePrefix}-group`, VoiceConnectorItems: items },
        physicalResourceId: cr.PhysicalResourceId.fromResponse("VoiceConnectorGroup.VoiceConnectorGroupId"),
      },
      onUpdate: {
        service: SDK,
        action: "UpdateVoiceConnectorGroup",
        parameters: { VoiceConnectorGroupId: new cr.PhysicalResourceIdReference(), Name: `${cfg.namePrefix}-group`, VoiceConnectorItems: items },
        physicalResourceId: cr.PhysicalResourceId.fromResponse("VoiceConnectorGroup.VoiceConnectorGroupId"),
      },
      onDelete: { service: SDK, action: "DeleteVoiceConnectorGroup", parameters: { VoiceConnectorGroupId: new cr.PhysicalResourceIdReference() } },
      policy,
      installLatestAwsSdk: false,
    });
    new CfnOutput(this, "VoiceConnectorGroupId", { value: group.getResponseField("VoiceConnectorGroup.VoiceConnectorGroupId") });
  }
}

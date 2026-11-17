// LFG SIP trunk for the Avaya SBCE during coexistence: Amazon Chime SDK Voice Connector.
// CloudFormation has no resource types for Chime SDK Voice, so each piece is an SDK call made by
// a custom resource. This is the first cut from the 2025 proof of concept; see README.md for what
// production needs.
import * as fs from "fs";
import * as path from "path";
import { CfnOutput, Stack, StackProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import * as cr from "aws-cdk-lib/custom-resources";

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

const SDK = "ChimeSDKVoice";
const policy = cr.AwsCustomResourcePolicy.fromSdkCalls({ resources: cr.AwsCustomResourcePolicy.ANY_RESOURCE });

export class VoiceConnectorStack extends Stack {
  constructor(scope: Construct, id: string, props: StackProps & { cfg: EnvConfig }) {
    super(scope, id, props);
    const { cfg } = props;

    // TODO: one Voice Connector per entry in cfg.voiceConnectors, plus a Voice Connector group.
    const first = cfg.voiceConnectors[0];
    const vc = new cr.AwsCustomResource(this, "VoiceConnector", {
      onCreate: {
        service: SDK,
        action: "CreateVoiceConnector",
        parameters: { Name: `${cfg.namePrefix}-${first.key}`, AwsRegion: first.awsRegion, RequireEncryption: false },
        physicalResourceId: cr.PhysicalResourceId.fromResponse("VoiceConnector.VoiceConnectorId"),
      },
      policy,
      installLatestAwsSdk: false,
    });
    const voiceConnectorId = vc.getResponseField("VoiceConnector.VoiceConnectorId");

    new cr.AwsCustomResource(this, "Termination", {
      onCreate: {
        service: SDK,
        action: "PutVoiceConnectorTermination",
        parameters: {
          VoiceConnectorId: voiceConnectorId,
          Termination: { CidrAllowedList: cfg.termination.cidrAllowedList, CallingRegions: cfg.termination.callingRegions, CpsLimit: 1, Disabled: false },
        },
        physicalResourceId: cr.PhysicalResourceId.of("termination"),
      },
      policy,
      installLatestAwsSdk: false,
    });

    new cr.AwsCustomResource(this, "Origination", {
      onCreate: {
        service: SDK,
        action: "PutVoiceConnectorOrigination",
        parameters: {
          VoiceConnectorId: voiceConnectorId,
          Origination: { Disabled: false, Routes: cfg.origination.map((o) => ({ Host: o.host, Port: 5060, Protocol: "UDP", Priority: 1, Weight: 1 })) },
        },
        physicalResourceId: cr.PhysicalResourceId.of("origination"),
      },
      policy,
      installLatestAwsSdk: false,
    });

    // Termination credentials straight from config (works in the PoC account).
    new cr.AwsCustomResource(this, "TerminationCredentials", {
      onCreate: {
        service: SDK,
        action: "PutVoiceConnectorTerminationCredentials",
        parameters: {
          VoiceConnectorId: voiceConnectorId,
          Credentials: [{ Username: cfg.terminationCredentials.username, Password: cfg.terminationCredentials.legacyPassword }],
        },
        physicalResourceId: cr.PhysicalResourceId.of("credentials"),
      },
      policy,
      installLatestAwsSdk: false,
    });

    // TODO: logging (SIP message logs and media metric logs), outputs for the outbound host name.
    new CfnOutput(this, "VoiceConnectorId", { value: voiceConnectorId });
  }
}

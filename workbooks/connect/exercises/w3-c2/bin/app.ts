// CDK entry point. Usage: npx cdk synth -c env=prod   (synth runs offline; nothing is deployed here)
import { App } from "aws-cdk-lib";
import { VoiceConnectorStack, loadEnvironment } from "../lib/voice-connector-stack";

const app = new App();
const envName = app.node.tryGetContext("env");
if (!envName) {
  throw new Error('Missing required context: env. Pass via "-c env=<name>" (e.g. "npx cdk synth -c env=prod").');
}
const cfg = loadEnvironment(envName);
new VoiceConnectorStack(app, `LfgVoiceConnector-${envName}`, { env: { account: cfg.account, region: cfg.region }, cfg });

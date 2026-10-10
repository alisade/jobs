// Print the synthesized template for one environment: make synth ENV=prod
import * as path from "path";
import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { HelpDeskStack, loadConfig, EnvName } from "../lib/helpdesk-stack";

const envName = (process.env.ENV || "dev") as EnvName;
const { config, flowTemplate } = loadConfig(path.resolve(__dirname, "../.."));
const e = config.envs[envName] || {};
const app = new App();
const stack = new HelpDeskStack(app, `HelpDesk-${envName}`, { envName, config, flowTemplate, env: { account: e.account, region: e.region } });
process.stdout.write(JSON.stringify(Template.fromStack(stack).toJSON(), null, 2) + "\n");

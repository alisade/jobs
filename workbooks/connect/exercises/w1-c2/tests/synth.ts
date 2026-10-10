// Shared synth helper for the w1-c2 tests: builds the stack offline and returns its template.
import * as path from "path";
import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { HelpDeskStack, loadConfig, EnvName } from "../lib/helpdesk-stack";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");

export function synth(envName: EnvName = "dev", mutate?: (cfg: any) => void, flowTemplate?: string) {
  const loaded = loadConfig(root);
  const cfg = JSON.parse(JSON.stringify(loaded.config));
  if (mutate) mutate(cfg);
  const app = new App();
  const e = cfg.envs[envName] || { account: "111122223333", region: "us-east-1" };
  const stack = new HelpDeskStack(app, `HelpDesk-${envName}`, {
    envName,
    config: cfg,
    flowTemplate: flowTemplate ?? loaded.flowTemplate,
    env: { account: e.account, region: e.region },
  });
  return { template: Template.fromStack(stack), stack, cfg };
}

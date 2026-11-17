import { App } from "aws-cdk-lib";
import { Template, Annotations } from "aws-cdk-lib/assertions";
import { buildApp } from "../lib/app";

export function synth(env = "dev", imageTag = "v2.4.0") {
  const app = new App({ context: { env, imageTag } });
  const stacks = buildApp(app);
  return {
    app,
    runtime: Template.fromStack(stacks.runtime),
    repo: Template.fromStack(stacks.repo),
    runtimeAnn: Annotations.fromStack(stacks.runtime),
    stacks,
  };
}

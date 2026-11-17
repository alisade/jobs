// Lighthouse helpdesk agent on AgentCore Runtime + Gateway. Pilot stack written against dev by hand.
// TODO (see README): immutable scanned repo with lifecycle and pull-only cross-account policy,
// fail-fast env and imageTag context, least-privilege execution role, isolated VPC with interface
// endpoints, versioned endpoints from config, JWT gateway with the user-directory Lambda target,
// tags, and the NoWildcardActions aspect.
import { App, IAspect, Stack, StackProps } from "aws-cdk-lib";
import { Construct, IConstruct } from "constructs";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as agentcore from "aws-cdk-lib/aws-bedrockagentcore";
import config from "../config/envs.json";

export type EnvName = keyof typeof config.envs;

/** Fails synth when an IAM statement grants "*" or "service:*" actions. */
export class NoWildcardActions implements IAspect {
  visit(_node: IConstruct): void {
    // TODO
  }
}

export class ImageRepoStack extends Stack {
  readonly repository: ecr.Repository;
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    this.repository = new ecr.Repository(this, "AgentRepo", { repositoryName: config.sharedServices.repositoryName });
  }
}

export interface RuntimeStackProps extends StackProps { envName: EnvName; imageTag: string; }

export class LighthouseRuntimeStack extends Stack {
  constructor(scope: Construct, id: string, props: RuntimeStackProps) {
    const cfg = config.envs[props.envName];
    super(scope, id, { ...props, env: { account: cfg.account, region: cfg.region } });
    const ss = config.sharedServices;
    const repo = ecr.Repository.fromRepositoryAttributes(this, "AgentRepo", {
      repositoryArn: `arn:aws:ecr:${ss.region}:${ss.account}:repository/${ss.repositoryName}`,
      repositoryName: ss.repositoryName,
    });
    const runtime = new agentcore.Runtime(this, "Runtime", {
      runtimeName: "lighthouse_helpdesk",
      agentRuntimeArtifact: agentcore.AgentRuntimeArtifact.fromEcrRepository(repo, props.imageTag),
    });
    runtime.addEndpoint("prod");
  }
}

export function buildApp(app: App): { repo: ImageRepoStack; runtime: LighthouseRuntimeStack } {
  const envName = (app.node.tryGetContext("env") || "dev") as EnvName;
  const imageTag = app.node.tryGetContext("imageTag") || "latest";
  const ss = config.sharedServices;
  const repo = new ImageRepoStack(app, "LighthouseImageRepo", { env: { account: ss.account, region: ss.region } });
  const runtime = new LighthouseRuntimeStack(app, `LighthouseRuntime-${envName}`, { envName, imageTag });
  return { repo, runtime };
}

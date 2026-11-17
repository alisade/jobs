import { App, Aspects, Stack, StackProps, Tags, RemovalPolicy, Duration, Annotations, IAspect, CfnResource } from "aws-cdk-lib";
import { Construct, IConstruct } from "constructs";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as agentcore from "aws-cdk-lib/aws-bedrockagentcore";
import * as path from "path";
import config from "../config/envs.json";

export type EnvName = keyof typeof config.envs;
type EnvConfig = (typeof config.envs)[EnvName];

const IMAGE_TAG = /^(v\d+\.\d+\.\d+|[0-9a-f]{12,40})$/;

/** Fails synth when an IAM statement grants "*" or "service:*" actions. */
export class NoWildcardActions implements IAspect {
  visit(node: IConstruct): void {
    if (!(node instanceof CfnResource)) return;
    if (node.cfnResourceType !== "AWS::IAM::Policy" && node.cfnResourceType !== "AWS::IAM::Role") return;
    const stack = Stack.of(node);
    const rendered = stack.resolve((node as any)._toCloudFormation());
    const props: any = Object.values<any>(rendered.Resources ?? {})[0]?.Properties ?? {};
    const docs: any[] = [];
    if (props.PolicyDocument) docs.push(props.PolicyDocument);
    for (const p of props.Policies ?? []) docs.push(p.PolicyDocument);
    for (const d of docs) {
      for (const st of d.Statement ?? []) {
        if (st.Effect !== "Allow") continue;
        const actions = ([] as string[]).concat(st.Action ?? []);
        const bad = actions.filter((a) => typeof a === "string" && (a === "*" || a.endsWith(":*")));
        if (bad.length) Annotations.of(node).addError(`wildcard IAM action(s) ${bad.join(", ")} are not allowed`);
      }
    }
  }
}

export class ImageRepoStack extends Stack {
  readonly repository: ecr.Repository;
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);
    this.repository = new ecr.Repository(this, "AgentRepo", {
      repositoryName: config.sharedServices.repositoryName,
      imageTagMutability: ecr.TagMutability.IMMUTABLE,
      imageScanOnPush: true,
      removalPolicy: RemovalPolicy.RETAIN,
      lifecycleRules: [
        { description: "expire untagged", tagStatus: ecr.TagStatus.UNTAGGED, maxImageAge: Duration.days(7), rulePriority: 1 },
        { description: "keep last 50 images", tagStatus: ecr.TagStatus.ANY, maxImageCount: 50, rulePriority: 2 },
      ],
    });
    const accounts = Object.values(config.envs).map((e) => e.account);
    this.repository.addToResourcePolicy(new iam.PolicyStatement({
      sid: "WorkloadAccountsPull",
      principals: accounts.map((a) => new iam.AccountPrincipal(a)),
      actions: ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"],
    }));
  }
}

export interface RuntimeStackProps extends StackProps { envName: EnvName; imageTag: string; }

export class LighthouseRuntimeStack extends Stack {
  constructor(scope: Construct, id: string, props: RuntimeStackProps) {
    const cfg: EnvConfig = config.envs[props.envName];
    super(scope, id, { ...props, env: { account: cfg.account, region: cfg.region } });
    const ss = config.sharedServices;

    const vpc = new ec2.Vpc(this, "AgentVpc", {
      ipAddresses: ec2.IpAddresses.cidr(cfg.vpcCidr), maxAzs: 2, natGateways: 0,
      subnetConfiguration: [{ name: "agents", subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 }],
    });
    const endpointSg = new ec2.SecurityGroup(this, "EndpointSg", { vpc, allowAllOutbound: false, description: "interface endpoints" });
    endpointSg.addIngressRule(ec2.Peer.ipv4(cfg.vpcCidr), ec2.Port.tcp(443), "HTTPS from the agent VPC");
    const iface: Record<string, ec2.InterfaceVpcEndpointAwsService> = {
      BedrockRuntime: ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
      AgentCore: new ec2.InterfaceVpcEndpointAwsService("bedrock-agentcore"),
      EcrApi: ec2.InterfaceVpcEndpointAwsService.ECR,
      EcrDocker: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
      Logs: ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
      Sts: ec2.InterfaceVpcEndpointAwsService.STS,
    };
    for (const [name, service] of Object.entries(iface)) {
      vpc.addInterfaceEndpoint(name, { service, privateDnsEnabled: true, securityGroups: [endpointSg] });
    }
    vpc.addGatewayEndpoint("S3", { service: ec2.GatewayVpcEndpointAwsService.S3 });

    const repo = ecr.Repository.fromRepositoryAttributes(this, "AgentRepo", {
      repositoryArn: `arn:aws:ecr:${ss.region}:${ss.account}:repository/${ss.repositoryName}`,
      repositoryName: ss.repositoryName,
    });

    const role = new iam.Role(this, "RuntimeRole", {
      assumedBy: new iam.ServicePrincipal("bedrock-agentcore.amazonaws.com", {
        conditions: { StringEquals: { "aws:SourceAccount": cfg.account } },
      }),
      description: `Lighthouse helpdesk runtime (${props.envName})`,
    });
    role.addToPolicy(new iam.PolicyStatement({
      sid: "InvokeApprovedModel",
      actions: ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      resources: [
        `arn:aws:bedrock:${cfg.region}:${cfg.account}:inference-profile/${cfg.inferenceProfileId}`,
        `arn:aws:bedrock:*::foundation-model/${cfg.foundationModelId}`,
      ],
    }));

    const runtime = new agentcore.Runtime(this, "Runtime", {
      runtimeName: `lighthouse_helpdesk_${props.envName}`,
      agentRuntimeArtifact: agentcore.AgentRuntimeArtifact.fromEcrRepository(repo, props.imageTag),
      executionRole: role,
      networkConfiguration: agentcore.RuntimeNetworkConfiguration.usingVpc(this, { vpc, vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED } }),
      environmentVariables: { LIGHTHOUSE_ENV: props.envName, MODEL_ID: cfg.inferenceProfileId },
      description: `Lighthouse helpdesk agent ${props.imageTag}`,
    });
    for (const [name, version] of Object.entries(cfg.endpoints)) {
      new agentcore.RuntimeEndpoint(this, `Endpoint-${name}`, {
        agentRuntimeId: runtime.agentRuntimeId, endpointName: name,
        ...(version ? { agentRuntimeVersion: version } : {}),
      });
    }

    const directory = new lambda.Function(this, "UserDirectory", {
      runtime: lambda.Runtime.PYTHON_3_12, architecture: lambda.Architecture.ARM_64, handler: "index.handler",
      code: lambda.Code.fromAsset(path.join(__dirname, "..", "lambda", "user-directory")), timeout: Duration.seconds(10),
    });
    const gateway = new agentcore.Gateway(this, "Gateway", {
      gatewayName: `lighthouse-tools-${props.envName}`,
      authorizerConfiguration: agentcore.GatewayAuthorizer.usingCustomJwt({
        discoveryUrl: cfg.idpDiscoveryUrl, allowedAudience: [cfg.gatewayAudience],
      }),
    });
    agentcore.GatewayTarget.forLambda(this, "UserDirectoryTarget", {
      gateway, gatewayTargetName: "user-directory", lambdaFunction: directory,
      toolSchema: agentcore.ToolSchema.fromInline([{
        name: "find_user",
        description: "Find an employee by work email. Returns whether the user exists.",
        inputSchema: { type: agentcore.SchemaDefinitionType.OBJECT, required: ["email"],
          properties: { email: { type: agentcore.SchemaDefinitionType.STRING, description: "work email, name@harborpoint.example" } } },
      }]),
    } as any);

    Tags.of(this).add("Environment", props.envName);
    for (const [k, v] of Object.entries(config.tags)) Tags.of(this).add(k, v);
  }
}

/** Reads -c env and -c imageTag, failing fast with the exact fix when either is missing or wrong. */
export function buildApp(app: App): { repo: ImageRepoStack; runtime: LighthouseRuntimeStack } {
  const envName = app.node.tryGetContext("env");
  const names = Object.keys(config.envs);
  if (!envName || !names.includes(envName)) {
    throw new Error(`Missing or unknown context: env. Pass -c env=<name> (e.g. "npx cdk synth -c env=dev -c imageTag=v2.4.0"). Available: ${names.join(", ")}`);
  }
  const imageTag = app.node.tryGetContext("imageTag");
  if (!imageTag || !IMAGE_TAG.test(imageTag)) {
    throw new Error(`Missing or invalid context: imageTag. Pass -c imageTag=vX.Y.Z or a git sha (12-40 hex); mutable tags such as "latest" are not deployable. Got: ${imageTag}`);
  }
  const ss = config.sharedServices;
  const repo = new ImageRepoStack(app, "LighthouseImageRepo", { env: { account: ss.account, region: ss.region } });
  const runtime = new LighthouseRuntimeStack(app, `LighthouseRuntime-${envName}`, { envName, imageTag });
  Aspects.of(app).add(new NoWildcardActions());
  return { repo, runtime };
}

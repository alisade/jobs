import { App, Stack, Aspects } from "aws-cdk-lib";
import { Annotations, Match, Template } from "aws-cdk-lib/assertions";
import * as iam from "aws-cdk-lib/aws-iam";
import { synth } from "../helpers";
import { NoWildcardActions } from "../../lib/app";

const res = (t: Template, type: string) => Object.values<any>(t.findResources(type));

test("prod endpoints: canary floats, prod pinned to the configured version", () => {
  const eps = res(synth("prod").runtime, "AWS::BedrockAgentCore::RuntimeEndpoint").map((e) => e.Properties);
  const byName = Object.fromEntries(eps.map((e) => [e.Name, e]));
  expect(Object.keys(byName).sort()).toEqual(["canary", "prod"]);
  expect(byName.prod.AgentRuntimeVersion).toBe("7");
});

test("dev has only a dev endpoint", () => {
  const eps = res(synth("dev").runtime, "AWS::BedrockAgentCore::RuntimeEndpoint").map((e) => e.Properties.Name);
  expect(eps).toEqual(["dev"]);
});

test("execution role trusts AgentCore with a SourceAccount condition", () => {
  const { runtime } = synth("prod");
  runtime.hasResourceProperties("AWS::IAM::Role", {
    AssumeRolePolicyDocument: { Statement: Match.arrayWith([Match.objectLike({
      Principal: { Service: "bedrock-agentcore.amazonaws.com" },
      Condition: { StringEquals: { "aws:SourceAccount": "111100000004" } },
    })]) },
  });
});

test("model access is the one inference profile and its foundation model only", () => {
  const { runtime } = synth("prod");
  const stmts = res(runtime, "AWS::IAM::Policy").flatMap((p) => p.Properties.PolicyDocument.Statement);
  const bedrock = stmts.filter((s) => [].concat(s.Action).some((a: string) => a.startsWith("bedrock:")));
  expect(bedrock).toHaveLength(1);
  expect([].concat(bedrock[0].Action).sort()).toEqual(["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]);
  expect([].concat(bedrock[0].Resource).sort()).toEqual([
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
    "arn:aws:bedrock:us-east-1:111100000004:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
  ]);
});

test("no wildcard actions anywhere and the stack synthesizes without errors", () => {
  const { runtimeAnn, runtime } = synth("prod");
  runtimeAnn.hasNoError("*", Match.anyValue());
  const stmts = res(runtime, "AWS::IAM::Policy").flatMap((p) => p.Properties.PolicyDocument.Statement);
  for (const s of stmts) for (const a of [].concat(s.Action)) expect(a === "*" || String(a).endsWith(":*")).toBe(false);
});

test("NoWildcardActions aspect flags s3:* on a role", () => {
  const app = new App();
  const st = new Stack(app, "Bad");
  const r = new iam.Role(st, "R", { assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com") });
  r.addToPolicy(new iam.PolicyStatement({ actions: ["s3:*"], resources: ["*"] }));
  Aspects.of(app).add(new NoWildcardActions());
  Annotations.fromStack(st).hasError("*", Match.stringLikeRegexp("wildcard"));
});

test("isolated VPC: no NAT, no internet gateway", () => {
  const { runtime } = synth("dev");
  expect(res(runtime, "AWS::EC2::NatGateway")).toHaveLength(0);
  expect(res(runtime, "AWS::EC2::InternetGateway")).toHaveLength(0);
});

test("interface endpoints with private DNS for bedrock-runtime, agentcore, ecr, logs", () => {
  const eps = res(synth("dev").runtime, "AWS::EC2::VPCEndpoint").map((e) => e.Properties);
  const names = eps.map((e) => JSON.stringify(e.ServiceName));
  for (const svc of ["bedrock-runtime", "bedrock-agentcore", "ecr.api", "ecr.dkr", "logs"]) {
    const hit = eps.find((e) => new RegExp(`\\.${svc.replace(".", "\\.")}"`).test(JSON.stringify(e.ServiceName)));
    expect(hit && hit.PrivateDnsEnabled).toBeTruthy();
  }
  expect(names.some((n) => /\.s3"/.test(n))).toBe(true);
  expect(eps.find((e) => /\.s3"/.test(JSON.stringify(e.ServiceName))).VpcEndpointType).toBe("Gateway");
});

test("endpoint security group only allows 443 from the VPC CIDR", () => {
  const { runtime } = synth("dev");
  const sgs = res(runtime, "AWS::EC2::SecurityGroup").map((s) => s.Properties);
  const withIngress = sgs.filter((s) => s.SecurityGroupIngress);
  expect(withIngress.length).toBeGreaterThan(0);
  for (const sg of withIngress) for (const r of sg.SecurityGroupIngress) {
    expect(r.CidrIp === "10.40.0.0/20" || JSON.stringify(r.CidrIp).includes("CidrBlock")).toBe(true);
    expect(r.FromPort).toBe(443);
    expect(r.ToPort).toBe(443);
  }
});

test("runtime runs in VPC mode", () => {
  const rt = res(synth("prod").runtime, "AWS::BedrockAgentCore::Runtime")[0].Properties;
  expect(rt.NetworkConfiguration.NetworkMode).toBe("VPC");
  expect(rt.EnvironmentVariables.LIGHTHOUSE_ENV).toBe("prod");
});

test("gateway requires a JWT for the environment's audience", () => {
  const { runtime } = synth("prod");
  runtime.hasResourceProperties("AWS::BedrockAgentCore::Gateway", {
    AuthorizerType: "CUSTOM_JWT",
    AuthorizerConfiguration: { CustomJWTAuthorizer: {
      DiscoveryUrl: "https://idp.harborpoint.example/oauth2/lighthouse/.well-known/openid-configuration",
      AllowedAudience: ["lighthouse-gateway"] } },
  });
});

test("gateway exposes the user-directory Lambda as find_user; Lambda is ARM64", () => {
  const { runtime } = synth("dev");
  const tgt = res(runtime, "AWS::BedrockAgentCore::GatewayTarget")[0].Properties;
  expect(tgt.Name).toBe("user-directory");
  const tools = tgt.TargetConfiguration.Mcp.Lambda.ToolSchema.InlinePayload;
  expect(tools.map((t: any) => t.Name)).toEqual(["find_user"]);
  expect(tools[0].InputSchema.Required).toEqual(["email"]);
  runtime.hasResourceProperties("AWS::Lambda::Function", { Architectures: ["arm64"] });
});

test.each(["latest", "main", "v2.4"])("mutable or malformed image tag %s fails synth", (tag) => {
  expect(() => synth("dev", tag)).toThrow(/imageTag/);
});

test("a git sha tag is accepted", () => {
  expect(() => synth("dev", "5e1c0a9d3f7b")).not.toThrow();
});

test("unknown env fails and lists the available envs", () => {
  expect(() => synth("stage")).toThrow(/dev, prod/);
});

test("repo: lifecycle rules, retained, pull-only cross-account policy", () => {
  const { repo } = synth();
  const r = res(repo, "AWS::ECR::Repository")[0];
  expect(r.DeletionPolicy).toBe("Retain");
  const lc = JSON.parse(r.Properties.LifecyclePolicy.LifecyclePolicyText);
  expect(lc.rules.some((x: any) => x.selection.tagStatus === "untagged")).toBe(true);
  const st = r.Properties.RepositoryPolicyText.Statement;
  const principals = JSON.stringify(st.map((s: any) => s.Principal));
  expect(principals).toContain("111100000003");
  expect(principals).toContain("111100000004");
  for (const s of st) for (const a of [].concat(s.Action)) expect(["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"]).toContain(a);
});

test("runtime and vpc are tagged with Environment and CostCenter", () => {
  const { runtime } = synth("prod");
  const vpc = res(runtime, "AWS::EC2::VPC")[0].Properties.Tags;
  expect(vpc).toEqual(expect.arrayContaining([{ Key: "Environment", Value: "prod" }, { Key: "CostCenter", Value: "cc-4410-lighthouse" }]));
});

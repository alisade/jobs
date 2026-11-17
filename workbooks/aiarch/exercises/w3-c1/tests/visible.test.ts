import { synth } from "./helpers";

test("runtime pulls the immutable tag from the shared-services repo", () => {
  const { runtime } = synth("dev", "v2.4.0");
  const rt = Object.values<any>(runtime.findResources("AWS::BedrockAgentCore::Runtime"));
  expect(rt).toHaveLength(1);
  expect(rt[0].Properties.AgentRuntimeName).toBe("lighthouse_helpdesk_dev");
  const uri = JSON.stringify(rt[0].Properties.AgentRuntimeArtifact.ContainerConfiguration.ContainerUri);
  expect(uri).toMatch(/111100000002\.dkr\.ecr\.us-east-1\..*lighthouse\/helpdesk-agent:v2\.4\.0/);
});

test("repo is immutable and scanned", () => {
  const { repo } = synth();
  repo.hasResourceProperties("AWS::ECR::Repository", { ImageTagMutability: "IMMUTABLE", ImageScanningConfiguration: { ScanOnPush: true } });
});

test("missing env fails fast", () => {
  expect(() => synth("", "v2.4.0")).toThrow(/-c env=/);
});

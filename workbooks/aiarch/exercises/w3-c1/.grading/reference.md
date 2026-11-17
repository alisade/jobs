# Reference: aiarch/w3-c1

See `.grading/solution/lib/app.ts`. Notes: `RuntimeEndpoint` takes `agentRuntimeVersion` to pin;
`RuntimeNetworkConfiguration.usingVpc` creates the runtime security group; interface endpoints
add a VPC-CIDR ingress rule by default (`open: true`); the AgentCore interface endpoint service
name is `com.amazonaws.<region>.bedrock-agentcore`; the aspect renders each IAM resource with
`stack.resolve(node._toCloudFormation())` and checks Allow actions.

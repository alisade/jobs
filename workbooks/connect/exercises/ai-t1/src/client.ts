// Bedrock runtime client factory. Tests pass a fake HTTP handler; production uses the default one.
import { BedrockRuntimeClient } from "@aws-sdk/client-bedrock-runtime";

export function makeClient(requestHandler?: any): BedrockRuntimeClient {
  return new BedrockRuntimeClient({
    region: process.env.AWS_REGION || "us-east-1",
    ...(requestHandler ? { requestHandler, credentials: { accessKeyId: "test", secretAccessKey: "test" } } : {}),
  });
}

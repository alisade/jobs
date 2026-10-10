// Test helpers for connect/w3-c2: synthesize the stack offline and decode the SDK calls that
// AwsCustomResource stores as JSON strings (Create / Update / Delete) in the template.
import { App } from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import { VoiceConnectorStack, loadEnvironment, EnvConfig } from "../lib/voice-connector-stack";

export function synth(mutate?: (c: EnvConfig) => void): any {
  const cfg = loadEnvironment("prod");
  if (mutate) mutate(cfg);
  const app = new App();
  const stack = new VoiceConnectorStack(app, "LfgVoiceConnector-prod", { env: { account: cfg.account, region: cfg.region }, cfg });
  return Template.fromStack(stack).toJSON();
}

/** Render CloudFormation intrinsics to a string with ${Logical.Attr} placeholders. */
export function render(v: any): string {
  if (typeof v === "string") return v;
  if (v && v["Fn::Join"]) return v["Fn::Join"][1].map(render).join(v["Fn::Join"][0]);
  if (v && v["Fn::GetAtt"]) return "${" + v["Fn::GetAtt"].join(".") + "}";
  if (v && v.Ref) return "${" + v.Ref + "}";
  return JSON.stringify(v);
}

export type SdkCall = { logicalId: string; phase: "Create" | "Update" | "Delete"; service: string; action: string; parameters: any; physicalResourceId?: any; dependsOn: string[] };

export function sdkCalls(t: any): SdkCall[] {
  const out: SdkCall[] = [];
  for (const [id, r] of Object.entries<any>(t.Resources)) {
    if (r.Type !== "Custom::AWS") continue;
    for (const phase of ["Create", "Update", "Delete"] as const) {
      if (r.Properties[phase] === undefined) continue;
      const call = JSON.parse(render(r.Properties[phase]));
      out.push({ logicalId: id, phase, service: call.service, action: call.action.replace(/Command$/, ""), parameters: call.parameters, physicalResourceId: call.physicalResourceId, dependsOn: r.DependsOn || [] });
    }
  }
  return out;
}

export const byAction = (t: any, action: string, phase: "Create" | "Update" | "Delete" = "Create") =>
  sdkCalls(t).filter((c) => c.action === action && c.phase === phase);

/** The logical id of the CreateVoiceConnector resource a ${X.VoiceConnector.VoiceConnectorId} placeholder points at. */
export const vcRef = (s: string) => (/^\$\{([A-Za-z0-9]+)\.VoiceConnector\.VoiceConnectorId\}$/.exec(s) || [])[1];

/** Every logical id a resource transitively depends on (DependsOn edges). */
export function dependsOnClosure(t: any, id: string, seen = new Set<string>()): Set<string> {
  for (const d of t.Resources[id]?.DependsOn || []) if (!seen.has(d)) { seen.add(d); dependsOnClosure(t, d, seen); }
  return seen;
}

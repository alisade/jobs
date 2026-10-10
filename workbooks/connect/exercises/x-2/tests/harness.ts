// Loaders for the x-2 tests.
import * as fs from "fs";
import * as path from "path";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const config = () => JSON.parse(fs.readFileSync(path.join(root, "guardrail/helpdesk-guardrail.json"), "utf8"));
export const cases = (file = "evals/cases.jsonl") =>
  fs.readFileSync(path.isAbsolute(file) ? file : path.join(root, file), "utf8").trim().split("\n").map((l) => JSON.parse(l) as { input: string; expect: "ALLOW" | "BLOCK"; kind?: string });
export const env = () => Object.fromEntries(fs.readFileSync(path.join(root, "config/lambda.env"), "utf8").split("\n").filter((l) => /^[A-Z_]+=/.test(l)).map((l) => l.split("=") as [string, string]));

/** Bedrock CreateGuardrail limits for denied topics (API_GuardrailTopicConfig). */
export function topicLimitErrors(cfg: any): string[] {
  const errs: string[] = [];
  for (const t of cfg.topicPolicyConfig?.topicsConfig || []) {
    if (!t.name || t.name.length > 100 || !/^[0-9a-zA-Z\-_ !?.]+$/.test(t.name)) errs.push(`name ${JSON.stringify(t.name)}: 1-100 chars of [0-9a-zA-Z-_ !?.]`);
    if (!t.definition || t.definition.length > 200) errs.push(`${t.name}: definition must be 1-200 chars (${(t.definition || "").length})`);
    if ((t.examples || []).length > 5) errs.push(`${t.name}: at most 5 examples`);
    for (const e of t.examples || []) if (e.length < 1 || e.length > 100) errs.push(`${t.name}: example ${JSON.stringify(e)} must be 1-100 chars`);
    if (t.type !== "DENY") errs.push(`${t.name}: type must be DENY`);
  }
  if ((cfg.topicPolicyConfig?.topicsConfig || []).length > 30) errs.push("at most 30 topics");
  return errs;
}

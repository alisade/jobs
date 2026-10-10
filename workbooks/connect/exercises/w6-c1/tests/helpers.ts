import * as fs from "fs";
import * as path from "path";
import { CompliancePolicy, ContactRecord } from "../src/types";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const analysisDir = path.join(root, "fixtures/analysis");
export const policy: CompliancePolicy = JSON.parse(fs.readFileSync(path.join(root, "config/compliance-policy.json"), "utf8"));
export const contacts: Record<string, ContactRecord> = JSON.parse(fs.readFileSync(path.join(root, "config/contacts.json"), "utf8")).contacts;
export const cid = (n: number) => `4c1d2e3f-${String(n).padStart(4, "0")}-4a5b-9c8d-${String(n).padStart(12, "0")}`;
export const fileFor = (n: number) => {
  const name = fs.readdirSync(analysisDir).find((f) => f.startsWith(cid(n)))!;
  return { key: path.join(analysisDir, name), body: JSON.parse(fs.readFileSync(path.join(analysisDir, name), "utf8")) };
};
export const segmentEvents = () =>
  fs.readFileSync(path.join(root, "fixtures/segments/realtime-2026-10-06.jsonl"), "utf8").trim().split("\n").map((l) => JSON.parse(l));
export const noSleep = async () => undefined;

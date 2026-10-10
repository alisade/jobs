// make setup: generate the incident bundle in incident/ from this checkout (deterministic).
import * as fs from "fs";
import * as path from "path";
import { execFileSync } from "child_process";

const root = path.resolve(__dirname, "..");
const inc = path.join(root, "incident");
fs.rmSync(inc, { recursive: true, force: true });
fs.mkdirSync(inc, { recursive: true });
execFileSync(process.execPath, [path.join(root, "scripts/ts-run.js"), path.join(root, "scripts/replay.ts"), "--out", inc], { stdio: "ignore" });
const w = (f: string, s: string) => fs.writeFileSync(path.join(inc, f), s);

w("PAGE.txt", `#lfg-helpdesk-ai  Tue 2026-10-07

[09:12] Priya N. (Finance BP, London): the portal chat answered my "map the finance drive"
        question with something about changing payroll bank accounts in Workday?? that looks like
        an HR-only article. screenshot attached (HD-2290)
[09:40] Marcus T. (Controllership): it told me to call the desk to get an RSA token shipped.
        we retired RSA tokens in 2024. is the KB stale again?
[10:05] Ama O. (InfoSec): two reports of HR-restricted content shown to non-HR staff = potential
        data exposure. Treat as SEV-2. Who owns the retriever?
[10:11] Jon (data platform): KB ingestion ran fine overnight, 3 docs failed (attachments over
        the metadata size limit), unrelated. We shipped exporter 2026.10.05 yesterday, just a
        naming cleanup.
[10:20] Kenji (contact center eng): retriever code has not changed since 2026.09.22 (HD-2231,
        widen search). Bedrock invocation logs attached. Could the model be mixing articles?
[10:31] Ama O.: I need root cause, blast radius (which callers saw what) and the fix by EOD.
`);
w("release-2026.10.05.md", `# KB exporter release 2026.10.05 (data platform)

- DG-114: align metadata attribute names with the data governance naming standard
  (short lowercase names, no more than 4 characters where an abbreviation exists).
- Exporter now lower-cases region codes.
- Upgraded ServiceNow Table API client to 3.2.0.
Tested: unit tests green; ingestion job succeeded in dev (KB ingestion reports 0 failures).
`);
w("release-2026.09.22.md", `# Help desk retriever release 2026.09.22 (contact center eng)

- HD-2231: when the entitlement filter returns no chunks, widen the search so the bot can still
  answer (containment +3.1 pts in UAT).
- Lowered numberOfResults from 5 to 3 to cut prompt tokens.
`);
w("exporter-2026.10.05.diff", `--- a/src/exporter.ts
+++ b/src/exporter.ts
@@ -12,9 +12,10 @@ export function toKbObject(a: SnArticle): KbObject {
       metadataAttributes: {
         articleId: a.number,
-        department: a.u_department,
+        // 2026.10.05: align attribute names with the data governance naming standard (DG-114)
+        dept: a.u_department,
         audience: a.u_audience,
-        region: a.u_region,
+        region: a.u_region.toLowerCase(),
         status: a.workflow_state,
         updated: a.sys_updated_on.slice(0, 10),
`);
w("ingestion-jobs.json", JSON.stringify({ ingestionJobSummaries: [
  { ingestionJobId: "IJ7Q2K0DSA", dataSourceId: "DSLFGSNOW1", knowledgeBaseId: "KBLFGHELP01", status: "COMPLETE", startedAt: "2026-10-06T02:00:04Z", updatedAt: "2026-10-06T02:06:51Z",
    statistics: { numberOfDocumentsScanned: 1846, numberOfMetadataDocumentsScanned: 1846, numberOfNewDocumentsIndexed: 4, numberOfModifiedDocumentsIndexed: 1839, numberOfMetadataDocumentsModified: 1839, numberOfDocumentsDeleted: 0, numberOfDocumentsFailed: 3 },
    failureReasons: ["Metadata file for s3://lfg-helpdesk-kb/attachments/KB0050012-diagram.pdf exceeds the 10 KB limit", "Metadata file for s3://lfg-helpdesk-kb/attachments/KB0050019-runbook.pdf exceeds the 10 KB limit", "Metadata file for s3://lfg-helpdesk-kb/attachments/KB0050020-runbook.pdf exceeds the 10 KB limit"] },
  { ingestionJobId: "IJ5M9P1VRT", dataSourceId: "DSLFGSNOW1", knowledgeBaseId: "KBLFGHELP01", status: "COMPLETE", startedAt: "2026-10-05T02:00:03Z", updatedAt: "2026-10-05T02:03:12Z",
    statistics: { numberOfDocumentsScanned: 1842, numberOfMetadataDocumentsScanned: 1842, numberOfNewDocumentsIndexed: 2, numberOfModifiedDocumentsIndexed: 14, numberOfMetadataDocumentsModified: 14, numberOfDocumentsDeleted: 1, numberOfDocumentsFailed: 3 },
    failureReasons: ["Metadata file for s3://lfg-helpdesk-kb/attachments/KB0050012-diagram.pdf exceeds the 10 KB limit", "Metadata file for s3://lfg-helpdesk-kb/attachments/KB0050019-runbook.pdf exceeds the 10 KB limit", "Metadata file for s3://lfg-helpdesk-kb/attachments/KB0050020-runbook.pdf exceeds the 10 KB limit"] },
] }, null, 2) + "\n");
w("model-invocation-log-sample.json", JSON.stringify({
  schemaType: "ModelInvocationLog", schemaVersion: "1.0", timestamp: "2026-10-07T13:00:12Z", accountId: "111122223333", region: "us-east-1",
  requestId: "6f1d2c3b-9a8e-4d7f-8c6b-5a4e3d2c1b0a", operation: "Converse", modelId: "us.anthropic.claude-haiku-4-5-20251001-v1:0",
  input: { inputContentType: "application/json", inputBodyJson: { messages: [{ role: "user", content: [
    { text: "[1] <h1>Payroll bank account change (HR only)</h1>\n<p>HR case workers verify the employee in Workday, then update the bank account under Pay > Payment elections.</p>\n\n[2] <h1>Quarter-end close: SAP posting periods</h1>..." },
    { text: "Question: map the finance drive" }] }], inferenceConfig: { maxTokens: 300, temperature: 0 } }, inputTokenCount: 642 },
  output: { outputContentType: "application/json", outputBodyJson: { output: { message: { role: "assistant", content: [{ text: "CANNOT_ANSWER" }] } }, stopReason: "end_turn" }, outputTokenCount: 4 },
}, null, 2) + "\n");
w("dashboard.txt", `Help desk RAG - portal chat (CloudWatch dashboard export, 2026-10-07 11:00 UTC)

metric                          2026-10-04 (Sat)   2026-10-06 (Mon)   2026-10-07 (Tue, to 11:00)
retrieve calls / contact                1.02              1.31               1.34
filtered results = 0 (pct)              2.1%             31.0%              33.4%
unfiltered fallback used (pct)          2.1%             31.0%              33.4%
answers citing restricted article        0                 41                 22
CANNOT_ANSWER rate                      6.0%             12.8%              13.5%
containment (portal chat)              38.2%             33.0%              32.1%
by caller department, filtered=0:  Finance 88%  HR 91%  Legal 85%  IT 6%  Contractors 11%  Unverified 14%
`);
console.log("incident bundle written to incident/");

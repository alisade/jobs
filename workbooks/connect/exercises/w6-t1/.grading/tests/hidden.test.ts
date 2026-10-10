// Hidden tests for connect/w6-t1 (run from tests/__hidden__).
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { buildReport, listAnalysisKeys, toCsv } from "../../src/report";
import { LocalS3 } from "../../src/s3mirror";
import { cardNumbersIn, cfg, cid, root, s3 } from "../helpers";

const all = () => buildReport(s3(), cfg, "2026-09-20", "2026-10-07");

test("no Luhn-valid card number anywhere in the report, including ones the ML redaction missed", () => {
  expect(cardNumbersIn(toCsv(all()))).toEqual([]);
});
test("every key the report reads is a redacted analysis object", () => {
  const keys = listAnalysisKeys(s3(), cfg);
  expect(keys.length).toBeGreaterThan(0);
  for (const k of keys) expect(k).toMatch(/\/Analysis\/Voice\/Redacted\/.*_analysis_redacted_/);
});
test("names redacted by conversational analytics stay redacted", () => {
  const r = all().find((x) => x.contact_id === cid(4))!;
  expect(r.issue_snippet).not.toMatch(/Dana Ruiz/);
  expect(r.issue_snippet).toMatch(/\[PII\]/);
});
test("one row per contact even when both originals and redacted files exist", () => {
  const ids = all().map((r) => r.contact_id);
  expect(new Set(ids).size).toBe(ids.length);
});
test("date filter still works", () => {
  expect(buildReport(s3(), cfg, "2026-10-01", "2026-10-07").map((r) => r.date)).toEqual(["2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06", "2026-10-07"]);
});
test("non-PII snippets are unchanged", () => {
  expect(all().find((x) => x.contact_id === cid(9))!.issue_snippet).toBe("Printer on floor 12 jams on every job.");
});

describe("guards on a crafted mirror", () => {
  let dir: string;
  beforeEach(() => { dir = fs.mkdtempSync(path.join(os.tmpdir(), "w6t1-")); });
  afterEach(() => fs.rmSync(dir, { recursive: true, force: true }));
  const put = (key: string, doc: any) => {
    const p = path.join(dir, cfg.bucket, key);
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, JSON.stringify(doc));
  };
  const base = (output: string, text: string) => ({
    Version: "1.1.0", ContentMetadata: { Output: output }, JobStatus: "COMPLETED", Categories: { MatchedCategories: [] },
    ConversationCharacteristics: { Sentiment: { OverallSentiment: { CUSTOMER: 0 } } },
    Transcript: [{ ParticipantId: "CUSTOMER", Content: text, IssuesDetected: [{ Text: text }] }],
  });
  test("a body that says Raw is refused even under the Redacted/ prefix", () => {
    put(`${cfg.analysisPrefix}Redacted/2026/10/07/${cid(90)}_analysis_redacted_2026-10-07T10-00-00Z.json`, base("Raw", "card 4111 1111 1111 1111"));
    expect(buildReport(new LocalS3(dir), cfg, "2026-10-01", "2026-10-31")).toEqual([]);
  });
  test("an original under the voice prefix is never read", () => {
    put(`${cfg.analysisPrefix}2026/10/07/${cid(91)}_analysis_2026-10-07T10-00-00Z.json`, base("Raw", "hello"));
    expect(buildReport(new LocalS3(dir), cfg, "2026-10-01", "2026-10-31")).toEqual([]);
  });
  test("a re-analysed contact keeps only the latest redacted file", () => {
    put(`${cfg.analysisPrefix}Redacted/2026/10/07/${cid(92)}_analysis_redacted_2026-10-07T10-00-00Z.json`, base("Redacted", "first"));
    put(`${cfg.analysisPrefix}Redacted/2026/10/07/${cid(92)}_analysis_redacted_2026-10-07T11-00-00Z.json`, base("Redacted", "second"));
    const rows = buildReport(new LocalS3(dir), cfg, "2026-10-01", "2026-10-31");
    expect(rows.map((r) => r.issue_snippet)).toEqual(["second"]);
  });
});

describe("least privilege for the report job role", () => {
  const policy = () => JSON.parse(fs.readFileSync(path.join(root, "infra/report-job-policy.json"), "utf8"));
  const resources = (action: string) => policy().Statement.filter((s: any) => s.Effect === "Allow" && [].concat(s.Action).some((a: string) => a === action || a === "s3:*" || a === "*")).flatMap((s: any) => [].concat(s.Resource));
  test("GetObject is limited to the redacted analysis prefix", () => {
    const res = resources("s3:GetObject");
    expect(res.length).toBeGreaterThan(0);
    for (const r of res) {
      if (!r.startsWith("arn:aws:s3:::lfg-connect-us-east-1")) continue;
      expect(r).toMatch(/\/Analysis\/(Voice|Chat)\/Redacted\//);
    }
  });
  test("listing is limited to the redacted prefix", () => {
    const list = policy().Statement.filter((s: any) => [].concat(s.Action).includes("s3:ListBucket"));
    for (const s of list) {
      const prefixes = [].concat(((s.Condition || {}).StringLike || {})["s3:prefix"] || []);
      expect(prefixes.length).toBeGreaterThan(0);
      for (const p of prefixes as string[]) expect(p).toMatch(/Analysis\/(Voice|Chat)\/Redacted\//);
    }
  });
  test("report output permission is kept", () => {
    expect(resources("s3:PutObject")).toContain("arn:aws:s3:::lfg-qa-reports/qa-insights/*");
  });
});

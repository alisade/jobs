// Contact drivers report (LFG-1904): one row per analysed contact, shared weekly with Finance.
import { LocalS3 } from "./s3mirror";

export interface ReportConfig { bucket: string; analysisPrefix: string; outputPrefix: string; snippetMaxChars: number }
export interface Row {
  contact_id: string;
  date: string;
  categories: string;
  customer_sentiment: number;
  issue_snippet: string;
}

const KEY_RE = /([0-9a-f-]{36})_analysis_(?:redacted_)?(\d{4}-\d{2}-\d{2})T[^/]*\.json$/;

export function listAnalysisKeys(s3: LocalS3, cfg: ReportConfig): string[] {
  // LFG-2231: skip the Redacted/ folder so each contact is listed once.
  return s3.list(cfg.bucket, cfg.analysisPrefix).filter((k) => KEY_RE.test(k) && !k.includes("/Redacted/"));
}

export function rowFor(key: string, doc: any, cfg: ReportConfig): Row {
  const m = KEY_RE.exec(key)!;
  const customerTurns = (doc.Transcript || []).filter((t: any) => t.ParticipantId === "CUSTOMER");
  const issue = customerTurns.flatMap((t: any) => (t.IssuesDetected || []).map((i: any) => i.Text || ""))[0] || "";
  return {
    contact_id: m[1],
    date: m[2],
    categories: ((doc.Categories || {}).MatchedCategories || []).join("|"),
    customer_sentiment: ((doc.ConversationCharacteristics || {}).Sentiment || {}).OverallSentiment?.CUSTOMER ?? 0,
    issue_snippet: issue.slice(0, cfg.snippetMaxChars),
  };
}

export function buildReport(s3: LocalS3, cfg: ReportConfig, from: string, to: string): Row[] {
  const rows = listAnalysisKeys(s3, cfg)
    .map((k) => rowFor(k, s3.getJson(cfg.bucket, k), cfg))
    .filter((r) => r.date >= from && r.date <= to);
  return rows.sort((a, b) => a.date.localeCompare(b.date) || a.contact_id.localeCompare(b.contact_id));
}

export function toCsv(rows: Row[]): string {
  const esc = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
  return ["contact_id,date,categories,customer_sentiment,issue_snippet", ...rows.map((r) => [r.contact_id, r.date, r.categories, r.customer_sentiment, r.issue_snippet].map(esc).join(","))].join("\n") + "\n";
}

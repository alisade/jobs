// Contact drivers report (LFG-1904): one row per analysed contact, shared weekly with Finance.
// SEC-INC-7781 fix: read ONLY the redacted analysis files, verify each body says Redacted, keep one
// row per contact, and scrub any Luhn-valid card number the ML redaction missed.
import { LocalS3 } from "./s3mirror";

export interface ReportConfig { bucket: string; analysisPrefix: string; outputPrefix: string; snippetMaxChars: number }
export interface Row {
  contact_id: string;
  date: string;
  categories: string;
  customer_sentiment: number;
  issue_snippet: string;
}

const KEY_RE = /([0-9a-f-]{36})_analysis_redacted_(\d{4}-\d{2}-\d{2})T[^/]*\.json$/;

export function listAnalysisKeys(s3: LocalS3, cfg: ReportConfig): string[] {
  const redactedPrefix = `${cfg.analysisPrefix.replace(/\/?$/, "/")}Redacted/`;
  return s3.list(cfg.bucket, redactedPrefix).filter((k) => KEY_RE.test(k));
}

function luhn(d: string): boolean {
  let s = 0;
  for (let i = 0; i < d.length; i++) {
    let x = d.charCodeAt(d.length - 1 - i) - 48;
    if (i % 2 === 1) { x *= 2; if (x > 9) x -= 9; }
    s += x;
  }
  return s % 10 === 0;
}

/** Defense in depth: the analytics redaction is ML-based and can miss a card number. */
export function scrubCards(text: string): string {
  return text.replace(/\b(?:\d[ -]?){12,18}\d\b/g, (m) => {
    const d = m.replace(/[ -]/g, "");
    return d.length >= 13 && d.length <= 19 && luhn(d) ? "[PII]" : m;
  });
}

export function rowFor(key: string, doc: any, cfg: ReportConfig): Row | null {
  const m = KEY_RE.exec(key);
  if (!m || !doc || !doc.ContentMetadata || doc.ContentMetadata.Output !== "Redacted") return null;
  const customerTurns = (doc.Transcript || []).filter((t: any) => t.ParticipantId === "CUSTOMER");
  const issue = customerTurns.flatMap((t: any) => (t.IssuesDetected || []).map((i: any) => i.Text || ""))[0] || "";
  return {
    contact_id: m[1],
    date: m[2],
    categories: ((doc.Categories || {}).MatchedCategories || []).join("|"),
    customer_sentiment: ((doc.ConversationCharacteristics || {}).Sentiment || {}).OverallSentiment?.CUSTOMER ?? 0,
    issue_snippet: scrubCards(issue).slice(0, cfg.snippetMaxChars),
  };
}

export function buildReport(s3: LocalS3, cfg: ReportConfig, from: string, to: string): Row[] {
  const latest = new Map<string, { key: string; row: Row }>();
  for (const k of listAnalysisKeys(s3, cfg)) {
    const row = rowFor(k, s3.getJson(cfg.bucket, k), cfg);
    if (!row || row.date < from || row.date > to) continue;
    const cur = latest.get(row.contact_id);
    if (!cur || k > cur.key) latest.set(row.contact_id, { key: k, row });
  }
  return [...latest.values()].map((x) => x.row).sort((a, b) => a.date.localeCompare(b.date) || a.contact_id.localeCompare(b.contact_id));
}

export function toCsv(rows: Row[]): string {
  const esc = (v: string | number) => `"${String(v).replace(/"/g, '""')}"`;
  return ["contact_id,date,categories,customer_sentiment,issue_snippet", ...rows.map((r) => [r.contact_id, r.date, r.categories, r.customer_sentiment, r.issue_snippet].map(esc).join(","))].join("\n") + "\n";
}

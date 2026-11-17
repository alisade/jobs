import * as fs from "fs";
import * as path from "path";
import { AnalysisFile, ContactAnalysis } from "./types";

/** Lower-case, drop punctuation, collapse whitespace: phrase matching is on normalized text. */
export function normalize(text: string): string {
  return text.toLowerCase().replace(/[^a-z0-9\[\] ]+/g, " ").replace(/\s+/g, " ").trim();
}

/** The contact id is the prefix of the S3 object name: <contactId>_analysis[_redacted]_<timestamp>.json */
export function contactIdFromKey(key: string): string {
  const base = path.basename(key);
  const m = /^([0-9a-f-]{36})_analysis_/.exec(base);
  if (!m) throw new InvalidAnalysisError(`not a conversational analytics output object name: ${base}`);
  return m[1];
}

export class InvalidAnalysisError extends Error {}
export class UnredactedInputError extends Error {}
export class IncompleteJobError extends Error {}

/**
 * Validate one output file. Only REDACTED, COMPLETED analyses may enter the QA pipeline:
 * the raw (original) file is the only complete copy of what the caller said, card numbers included.
 */
export function parseAnalysisFile(key: string, body: unknown): ContactAnalysis {
  const contactId = contactIdFromKey(key);
  const f = body as AnalysisFile;
  if (!f || typeof f !== "object" || !f.ContentMetadata || !Array.isArray(f.Transcript) || !f.ConversationCharacteristics) {
    throw new InvalidAnalysisError(`${contactId}: missing ContentMetadata, Transcript or ConversationCharacteristics`);
  }
  if (f.ContentMetadata.Output !== "Redacted" || /_analysis_redacted_/.test(path.basename(key)) === false) {
    throw new UnredactedInputError(`${contactId}: refusing a non-redacted analysis (Output=${f.ContentMetadata.Output})`);
  }
  if (f.JobStatus !== "COMPLETED") throw new IncompleteJobError(`${contactId}: JobStatus ${f.JobStatus}`);
  return { contactId, channel: f.Channel, file: f };
}

export interface Batch {
  analyses: ContactAnalysis[];
  rejected: { key: string; reason: "UNREDACTED" | "INCOMPLETE" | "INVALID"; message: string }[];
}

/** Load every *.json under dir (sorted by name, so results are deterministic). */
export function loadBatch(dir: string): Batch {
  const out: Batch = { analyses: [], rejected: [] };
  for (const name of fs.readdirSync(dir).filter((n) => n.endsWith(".json")).sort()) {
    const key = path.join(dir, name);
    try {
      out.analyses.push(parseAnalysisFile(key, JSON.parse(fs.readFileSync(key, "utf8"))));
    } catch (err) {
      const reason = err instanceof UnredactedInputError ? "UNREDACTED" : err instanceof IncompleteJobError ? "INCOMPLETE" : "INVALID";
      out.rejected.push({ key: name, reason, message: (err as Error).message });
    }
  }
  return out;
}

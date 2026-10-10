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
 * Validate one output file.
 * TODO: only REDACTED (ContentMetadata.Output "Redacted" AND a "_analysis_redacted_" object name),
 * COMPLETED analyses may enter the QA pipeline. Throw UnredactedInputError, IncompleteJobError or
 * InvalidAnalysisError so loadBatch can report the reason.
 */
export function parseAnalysisFile(key: string, body: unknown): ContactAnalysis {
  const contactId = contactIdFromKey(key);
  const f = body as AnalysisFile;
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

// Local stand-in for the Bedrock knowledge base (environment, not a suspect): indexes the exporter's
// objects and evaluates Retrieve the way the service does - vector ranking first (recorded scores
// per query in data/retrieval-scores.json), then the metadata filter, then numberOfResults.
// A filter on a key that no document carries simply matches nothing; it is not an error.
import * as fs from "fs";
import * as path from "path";
import { Filter, KbObject, RetrieveFn, RetrieveInput, RetrieveOutput } from "./types";

const DATA = path.resolve(__dirname, "../data");

export function matches(meta: Record<string, string>, f: Filter): boolean {
  if ("andAll" in f) return f.andAll.every((x) => matches(meta, x));
  if ("orAll" in f) return f.orAll.some((x) => matches(meta, x));
  if ("equals" in f) return meta[f.equals.key] !== undefined && meta[f.equals.key] === f.equals.value;
  if ("in" in f) return meta[f.in.key] !== undefined && f.in.value.includes(meta[f.in.key]);
  throw new Error(`kbsim: unsupported filter ${JSON.stringify(f)}`);
}

export function makeKb(objects: KbObject[], scoresFile = path.join(DATA, "retrieval-scores.json")) {
  const scores: Record<string, { articleId: string; score: number }[]> = JSON.parse(fs.readFileSync(scoresFile, "utf8"));
  const byId = new Map(objects.map((o) => [o.sidecar.metadataAttributes.articleId, o]));
  const calls: RetrieveInput[] = [];
  const retrieveFn: RetrieveFn = async (input) => {
    calls.push(JSON.parse(JSON.stringify(input)));
    const ranked = scores[input.retrievalQuery.text.toLowerCase()] || [];
    const f = input.retrievalConfiguration.vectorSearchConfiguration.filter;
    const out: RetrieveOutput["retrievalResults"] = [];
    for (const r of ranked) {
      const o = byId.get(r.articleId);
      if (!o) continue;
      if (f && !matches(o.sidecar.metadataAttributes, f)) continue;
      out.push({ content: { text: o.body }, location: { type: "S3", s3Location: { uri: `s3://lfg-helpdesk-kb/${o.key}` } }, metadata: { ...o.sidecar.metadataAttributes, "x-amz-bedrock-kb-source-uri": `s3://lfg-helpdesk-kb/${o.key}` }, score: r.score });
    }
    return { retrievalResults: out.slice(0, input.retrievalConfiguration.vectorSearchConfiguration.numberOfResults) };
  };
  return { retrieveFn, calls };
}

export function loadArticles() {
  return JSON.parse(fs.readFileSync(path.join(DATA, "servicenow-kb-export.json"), "utf8")).result;
}

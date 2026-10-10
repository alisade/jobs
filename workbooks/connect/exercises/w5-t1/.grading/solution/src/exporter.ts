// ServiceNow KB -> S3 exporter. Fixed: the sidecar attribute names are a contract with every
// consumer's metadata filter, so they come from config/metadata-schema.json and are checked.
import * as fs from "fs";
import * as path from "path";
import { KbObject, SnArticle } from "./types";

const SCHEMA: { attributes: Record<string, string> } = JSON.parse(fs.readFileSync(path.resolve(__dirname, "../config/metadata-schema.json"), "utf8"));

export function assertSidecarMatchesSchema(meta: Record<string, string>): void {
  const want = Object.keys(SCHEMA.attributes).sort().join(",");
  const got = Object.keys(meta).sort().join(",");
  if (want !== got) throw new Error(`sidecar attributes [${got}] do not match the KB metadata schema [${want}]`);
}

export function toKbObject(a: SnArticle): KbObject {
  const metadataAttributes = {
    articleId: a.number,
    department: a.u_department, // DG-114 rename reverted: consumers filter on "department" (HD-2290)
    audience: a.u_audience,
    region: a.u_region.toLowerCase(),
    status: a.workflow_state,
    updated: a.sys_updated_on.slice(0, 10),
  };
  assertSidecarMatchesSchema(metadataAttributes);
  return { key: `articles/${a.number}.html`, body: `<h1>${a.short_description}</h1>\n<p>${a.text}</p>`, sidecar: { metadataAttributes } };
}

export function exportAll(articles: SnArticle[]): KbObject[] {
  return articles.filter((a) => a.workflow_state !== "draft").map(toKbObject);
}

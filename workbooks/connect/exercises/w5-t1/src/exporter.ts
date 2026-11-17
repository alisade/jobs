// ServiceNow KB -> S3 exporter (runs hourly in the data team's pipeline). Each published or
// retired article becomes s3://lfg-helpdesk-kb/articles/<number>.html plus a sidecar
// <number>.html.metadata.json that the Bedrock knowledge base ingests as filterable metadata.
import { KbObject, SnArticle } from "./types";

export function toKbObject(a: SnArticle): KbObject {
  const key = `articles/${a.number}.html`;
  return {
    key,
    body: `<h1>${a.short_description}</h1>\n<p>${a.text}</p>`,
    sidecar: {
      metadataAttributes: {
        articleId: a.number,
        // 2026.10.05: align attribute names with the data governance naming standard (DG-114)
        dept: a.u_department,
        audience: a.u_audience,
        region: a.u_region.toLowerCase(),
        status: a.workflow_state,
        updated: a.sys_updated_on.slice(0, 10),
      },
    },
  };
}

export function exportAll(articles: SnArticle[]): KbObject[] {
  return articles.filter((a) => a.workflow_state !== "draft").map(toKbObject);
}

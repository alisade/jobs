import { BedrockAgentRuntimeClient, RetrieveCommand } from "@aws-sdk/client-bedrock-agent-runtime";
import { Article, PipelineConfig } from "./types";

/** Related KB articles for the agent / work note. Best effort: errors return []. */
export async function relatedArticles(client: BedrockAgentRuntimeClient, cfg: PipelineConfig, query: string): Promise<Article[]> {
  try {
    const out = await client.send(new RetrieveCommand({
      knowledgeBaseId: cfg.knowledgeBaseId,
      retrievalQuery: { text: query },
      retrievalConfiguration: {
        vectorSearchConfiguration: { numberOfResults: cfg.kbNumberOfResults, filter: { in: { key: "audience", value: cfg.kbAudience } } },
      },
    }));
    const seen = new Set<string>();
    const arts: Article[] = [];
    for (const r of out.retrievalResults || []) {
      const uri = r.location?.s3Location?.uri;
      const score = r.score ?? 0;
      if (!uri || score < cfg.kbMinScore || seen.has(uri)) continue;
      seen.add(uri);
      const md = (r.metadata || {}) as Record<string, unknown>;
      const title = (typeof md.title === "string" && md.title) || (typeof md.kb_number === "string" && md.kb_number) || uri.split("/").pop()!;
      arts.push({ title, uri, score });
    }
    return arts.sort((a, b) => b.score - a.score);
  } catch {
    return [];
  }
}

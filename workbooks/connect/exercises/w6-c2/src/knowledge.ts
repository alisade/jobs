import { BedrockAgentRuntimeClient } from "@aws-sdk/client-bedrock-agent-runtime";
import { Article, PipelineConfig } from "./types";

/**
 * TODO: Retrieve related KB articles (see README "Knowledge retrieval"): audience metadata filter,
 * numberOfResults, drop results under kbMinScore, dedupe by URI, title from metadata.title, then
 * metadata.kb_number, then the object name; sorted by score. Best effort: errors return [].
 */
export async function relatedArticles(client: BedrockAgentRuntimeClient, cfg: PipelineConfig, query: string): Promise<Article[]> {
  void client;
  throw new Error(`TODO: relatedArticles for ${cfg.knowledgeBaseId}: ${query}`);
}

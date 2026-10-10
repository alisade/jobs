// Merge, dedupe, entitle and rank knowledge suggestions from two recorded sources:
// agent assist (qconnect GetRecommendations) and a Bedrock Knowledge Bases Retrieve call.

export type AssistRecommendation = {
  recommendationId: string;
  relevanceScore?: number;
  relevanceLevel?: string;
  type?: string;
  document?: { contentReference?: { contentId?: string; knowledgeBaseId?: string }; title?: { text?: string }; excerpt?: { text?: string } };
};
export type KbResult = {
  content?: { text?: string };
  location?: { s3Location?: { uri?: string } };
  score?: number;
  metadata?: Record<string, string>;
};
export type CatalogEntry = { articleId: string; department: string };
export type Suggestion = { articleId: string; title: string; excerpt: string; score: number; source: "assist" | "kb" };

export type RankOptions = {
  catalog: Record<string, CatalogEntry>;
  departments: string[]; // the agent's entitlements; "all" articles are always visible
  minScore?: number;
  max?: number;
};

// TODO: see README "Knowledge suggestions": dedupe by article, entitlement filter, score floor,
// deterministic order, cap. The prototype just concatenates.
export function rankSuggestions(assist: AssistRecommendation[], kb: KbResult[], _opts: RankOptions): Suggestion[] {
  const a: Suggestion[] = (assist || []).map((r) => ({
    articleId: r.document?.contentReference?.contentId || r.recommendationId,
    title: r.document?.title?.text || "",
    excerpt: r.document?.excerpt?.text || "",
    score: r.relevanceScore || 0,
    source: "assist",
  }));
  const k: Suggestion[] = (kb || []).map((x) => ({
    articleId: x.metadata?.articleId || "",
    title: x.metadata?.title || "",
    excerpt: x.content?.text || "",
    score: x.score || 0,
    source: "kb",
  }));
  return a.concat(k);
}

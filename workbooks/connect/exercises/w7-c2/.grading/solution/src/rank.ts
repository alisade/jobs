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

const SOURCE_ORDER = { assist: 0, kb: 1 } as const;

export function rankSuggestions(assist: AssistRecommendation[], kb: KbResult[], opts: RankOptions): Suggestion[] {
  const minScore = opts.minScore ?? 0.4;
  const max = opts.max ?? 5;
  const allowed = new Set(opts.departments);
  const candidates: (Suggestion & { department: string })[] = [];

  for (const r of assist || []) {
    if (r.type && r.type !== "KNOWLEDGE_CONTENT") continue;
    const id = r.document?.contentReference?.contentId;
    if (!id) continue;
    const entry = opts.catalog[id];
    candidates.push({
      articleId: entry?.articleId ?? id,
      title: r.document?.title?.text ?? id,
      excerpt: r.document?.excerpt?.text ?? "",
      score: Number(r.relevanceScore ?? 0),
      source: "assist",
      department: entry?.department ?? "unknown",
    });
  }
  for (const k of kb || []) {
    const id = k.metadata?.articleId;
    if (!id) continue;
    const entry = opts.catalog[id];
    candidates.push({
      articleId: id,
      title: k.metadata?.title ?? id,
      excerpt: k.content?.text ?? "",
      score: Number(k.score ?? 0),
      source: "kb",
      department: entry?.department ?? k.metadata?.department ?? "unknown",
    });
  }

  const best = new Map<string, Suggestion & { department: string }>();
  for (const c of candidates) {
    if (!(c.department === "all" || allowed.has(c.department))) continue; // unknown department = not entitled
    if (!(c.score >= minScore)) continue;
    const prev = best.get(c.articleId);
    if (!prev || c.score > prev.score || (c.score === prev.score && SOURCE_ORDER[c.source] < SOURCE_ORDER[prev.source])) best.set(c.articleId, c);
  }
  return [...best.values()]
    .sort((a, b) => b.score - a.score || SOURCE_ORDER[a.source] - SOURCE_ORDER[b.source] || a.articleId.localeCompare(b.articleId))
    .slice(0, max)
    .map(({ department: _d, ...s }) => s);
}

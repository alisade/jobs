// lfg-sim-1: a DETERMINISTIC stand-in for the help desk AI agent, so tuning can be graded offline.
// It is not an LLM. It reproduces the levers that matter when you tune a real one:
//   - intent descriptions and few-shot examples decide what vocabulary each intent "understands";
//   - a confidence threshold trades misroutes against fallbacks (handoffs);
//   - retrieval topK / minScore decide whether the right article reaches the model;
//   - requiring citations (with a grounding check) turns would-be hallucinations into handoffs;
//   - every prompt token and every retrieved chunk costs latency.
// Treat this file as the environment. Tune tuning/agent.yaml, not this file.
import YAML from "yaml";

export type IntentDef = { name: string; description: string; examples?: string[] };
export type AgentConfig = {
  model: { temperature: number; maxTokens: number };
  intents: IntentDef[];
  classifier: { confidenceThreshold: number };
  retrieval: { topK: number; minScore: number };
  answer: { requireCitations: boolean };
};
export type EvalCase = {
  id: string;
  utterance: string;
  intent: string; // gold intent; "Fallback" = out of scope, must hand off
  retrieval?: { articleId: string; score: number }[]; // recorded KB ranking for HowTo cases
  goldArticle?: string;
};
export type CaseResult = {
  id: string;
  gold: string;
  predicted: string;
  confidence: number;
  outcome: "contained" | "routed" | "handoff" | "misrouted" | "hallucinated";
  latencyMs: number;
};
export type Metrics = {
  n: number;
  intentAccuracy: number; // predicted == gold (Fallback counts when gold is Fallback)
  containment: number; // contained / n
  misrouteRate: number; // confident wrong intent / n
  hallucinationRate: number; // ungrounded answers / n
  p95LatencyMs: number;
  promptTokens: number;
};

export const LIMITS = {
  descriptionTokens: 30, // longer descriptions are truncated (context budget per intent)
  examplesPerIntent: 6, // further examples are ignored
  exampleTokens: 20,
  baseLatencyMs: 250,
  perPromptTokenMs: 1,
  perChunkMs: 80,
  answerMs: 400,
};
export const CONTAINABLE = new Set(["ResetPassword", "UnlockAccount", "CheckTicketStatus", "HowTo"]);
export const ROUTED = new Set(["ReportOutage", "RequestAccess", "TalkToAgent"]);

const STOP = new Set("a an the i im i'm my me we our you your to for of on in at is are was were be been it its this that and or but can cant can't do does did dont don't not no with from please just get got need want have has had how what when where why who which will would could should any some there their them they he she his her as by up so if about again still also".split(" "));

export function tokens(text: string): string[] {
  return (text.toLowerCase().match(/[a-z0-9]+/g) || [])
    .filter((t) => !STOP.has(t))
    .map((t) => (t.length > 4 ? t.replace(/(ing|ed|es|s)$/, "") : t));
}

export function loadConfig(yamlText: string): AgentConfig {
  const c = YAML.parse(yamlText) as AgentConfig;
  if (!c || !Array.isArray(c.intents)) throw new Error("agent.yaml: intents[] missing");
  return c;
}

function intentVocab(c: AgentConfig): { name: string; vocab: Set<string> }[] {
  return c.intents.map((i) => {
    const desc = tokens(i.description || "").slice(0, LIMITS.descriptionTokens);
    const ex = (i.examples || []).slice(0, LIMITS.examplesPerIntent).flatMap((e) => tokens(e).slice(0, LIMITS.exampleTokens));
    return { name: i.name, vocab: new Set([...desc, ...ex]) };
  });
}

export function promptTokens(c: AgentConfig): number {
  return c.intents.reduce((n, i) => n + Math.min(tokens(i.description || "").length, LIMITS.descriptionTokens)
    + (i.examples || []).slice(0, LIMITS.examplesPerIntent).reduce((m, e) => m + Math.min(tokens(e).length, LIMITS.exampleTokens), 0), 0);
}

export function classify(c: AgentConfig, utterance: string): { intent: string; confidence: number } {
  const vocabs = intentVocab(c);
  const df = new Map<string, number>();
  for (const v of vocabs) for (const t of v.vocab) df.set(t, (df.get(t) || 0) + 1);
  const N = vocabs.length;
  const u = [...new Set(tokens(utterance))];
  const scored = vocabs
    .map((v) => ({ name: v.name, s: u.reduce((s, t) => s + (v.vocab.has(t) ? Math.log((N + 1) / (df.get(t)! + 0.5)) : 0), 0) / Math.sqrt(Math.max(u.length, 1)) }))
    .sort((a, b) => b.s - a.s || a.name.localeCompare(b.name));
  const [top, second] = [scored[0], scored[1] || { s: 0 }];
  const confidence = top && top.s > 0 ? top.s / (top.s + second.s + 0.5) : 0;
  if (!top || confidence < c.classifier.confidenceThreshold) return { intent: "Fallback", confidence };
  return { intent: top.name, confidence };
}

export function runCase(c: AgentConfig, k: EvalCase): CaseResult {
  const { intent, confidence } = classify(c, k.utterance);
  const pt = promptTokens(c);
  let latency = LIMITS.baseLatencyMs + pt * LIMITS.perPromptTokenMs;
  let outcome: CaseResult["outcome"];
  if (intent === "Fallback") outcome = "handoff";
  else if (intent !== k.intent) outcome = "misrouted";
  else if (ROUTED.has(intent)) outcome = "routed";
  else if (intent === "HowTo") {
    const got = (k.retrieval || []).slice(0, c.retrieval.topK).filter((r) => r.score >= c.retrieval.minScore);
    latency += got.length * LIMITS.perChunkMs + LIMITS.answerMs;
    if (!got.length) outcome = "handoff";
    else if (got.some((r) => r.articleId === k.goldArticle)) outcome = "contained";
    else outcome = c.answer.requireCitations ? "handoff" : "hallucinated";
  } else outcome = "contained";
  return { id: k.id, gold: k.intent, predicted: intent, confidence: Math.round(confidence * 1000) / 1000, outcome, latencyMs: latency };
}

export function evaluate(c: AgentConfig, cases: EvalCase[]): { metrics: Metrics; results: CaseResult[] } {
  const results = cases.map((k) => runCase(c, k));
  const n = results.length;
  const lat = results.map((r) => r.latencyMs).sort((a, b) => a - b);
  const p95 = lat[Math.min(lat.length - 1, Math.ceil(0.95 * lat.length) - 1)];
  const r3 = (x: number) => Math.round(x * 1000) / 1000;
  return {
    results,
    metrics: {
      n,
      intentAccuracy: r3(results.filter((r) => r.predicted === r.gold).length / n),
      containment: r3(results.filter((r) => r.outcome === "contained").length / n),
      misrouteRate: r3(results.filter((r) => r.outcome === "misrouted").length / n),
      hallucinationRate: r3(results.filter((r) => r.outcome === "hallucinated").length / n),
      p95LatencyMs: p95,
      promptTokens: promptTokens(c),
    },
  };
}

export function parseJsonl(text: string): EvalCase[] {
  return text.split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
}

// Local, deterministic stand-in for evaluating text against an Amazon Bedrock guardrail
// configuration (the CreateGuardrail request shape in guardrail/*.json). It is NOT Bedrock: it
// exists so the exercise can be graded offline. Treat it as the environment, not the suspect.
//
// Approximations (documented so you can reason about them):
// - Denied topics: Bedrock classifies with an ML model using the topic definition and sample
//   phrases. Here a topic matches when the input covers >= 75% of the content words of ANY of its
//   sample phrases (examples). Write sample phrases the way Bedrock needs them anyway: short,
//   specific, representative of what must be denied and nothing else.
// - Content filter PROMPT_ATTACK: a fixed list of jailbreak / injection markers, applied when the
//   input strength is LOW, MEDIUM or HIGH (NONE disables it).
// - Word filters: case-insensitive whole-phrase match.
// - Sensitive information: a few regexes for the PII types the config uses (EMAIL, PHONE,
//   PASSWORD, USERNAME). BLOCK blocks; ANONYMIZE masks (input continues); NONE detects only.

export type Action = "BLOCKED" | "ANONYMIZED" | "NONE";
export interface Assessment {
  action: "GUARDRAIL_INTERVENED" | "NONE";
  /** true when the input would be replaced by blockedInputMessaging */
  blocked: boolean;
  topics: { name: string; type: "DENY"; action: "BLOCKED"; matchedExample: string }[];
  contentFilters: { type: string; confidence: "HIGH"; action: "BLOCKED" }[];
  words: { match: string; action: "BLOCKED" }[];
  pii: { type: string; match: string; action: Action }[];
  outputText: string;
}

const STOP = new Set(("a an the my i me im i'm to for of is it its can cant can't could you your please what how do does did on in at and or " +
  "with this that be am are was were been will would should just so up out from as by about need want help hi hello there").split(" "));

export function contentWords(s: string): string[] {
  return s.toLowerCase().replace(/[^a-z0-9' ]+/g, " ").split(/\s+/).filter(Boolean)
    .map((w) => w.replace(/'s$/, "").replace(/'/g, ""))
    .filter((w) => w && !STOP.has(w))
    .map((w) => (w.length > 5 && w.endsWith("ing") ? w.slice(0, -3) : w.length > 4 && w.endsWith("ed") ? w.slice(0, -2) : w.length > 3 && w.endsWith("s") && !w.endsWith("ss") ? w.slice(0, -1) : w));
}

export function coverage(example: string, input: string): number {
  const e = new Set(contentWords(example));
  if (!e.size) return 0;
  const i = new Set(contentWords(input));
  let hit = 0;
  for (const w of e) if (i.has(w)) hit++;
  return hit / e.size;
}

const ATTACK_MARKERS = ["ignore previous instructions", "ignore all previous", "ignore your instructions", "you are now", "developer mode",
  "system prompt", "pretend you are", "act as an administrator", "disregard the rules", "jailbreak"];

const PII_RE: Record<string, RegExp> = {
  EMAIL: /\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b/gi,
  PHONE: /\+?\d[\d\s().-]{8,}\d/g,
  PASSWORD: /\b(?:password|passcode|pwd)\s*(?:is|=|:)\s*\S+/gi,
  USERNAME: /\b(?:username|user name|login|user id)\s*(?:is|=|:)\s*[a-z][a-z0-9._-]{2,}/gi,
};

export function evaluate(config: any, input: string): Assessment {
  const out: Assessment = { action: "NONE", blocked: false, topics: [], contentFilters: [], words: [], pii: [], outputText: input };
  for (const t of (config.topicPolicyConfig && config.topicPolicyConfig.topicsConfig) || []) {
    if (t.inputEnabled === false || t.inputAction === "NONE") continue;
    const hit = (t.examples || []).find((ex: string) => coverage(ex, input) >= 0.75);
    if (hit) out.topics.push({ name: t.name, type: "DENY", action: "BLOCKED", matchedExample: hit });
  }
  for (const f of (config.contentPolicyConfig && config.contentPolicyConfig.filtersConfig) || []) {
    if (f.type === "PROMPT_ATTACK" && f.inputStrength && f.inputStrength !== "NONE") {
      const l = input.toLowerCase();
      if (ATTACK_MARKERS.some((m) => l.includes(m))) out.contentFilters.push({ type: "PROMPT_ATTACK", confidence: "HIGH", action: "BLOCKED" });
    }
  }
  for (const w of (config.wordPolicyConfig && config.wordPolicyConfig.wordsConfig) || []) {
    const re = new RegExp(`\\b${String(w.text).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`, "i");
    if (re.test(input)) out.words.push({ match: w.text, action: "BLOCKED" });
  }
  for (const p of (config.sensitiveInformationPolicyConfig && config.sensitiveInformationPolicyConfig.piiEntitiesConfig) || []) {
    const re = PII_RE[p.type];
    if (!re) continue;
    const act = p.inputAction || p.action;
    for (const m of input.match(re) || []) {
      const action: Action = act === "BLOCK" ? "BLOCKED" : act === "ANONYMIZE" ? "ANONYMIZED" : "NONE";
      out.pii.push({ type: p.type, match: m, action });
      if (action === "ANONYMIZED") out.outputText = out.outputText.replace(m, `{${p.type}}`);
    }
  }
  const blocked = out.topics.length > 0 || out.contentFilters.length > 0 || out.words.length > 0 || out.pii.some((x) => x.action === "BLOCKED");
  out.blocked = blocked;
  const changed = out.pii.some((x) => x.action === "ANONYMIZED");
  out.action = blocked || changed ? "GUARDRAIL_INTERVENED" : "NONE";
  if (blocked) out.outputText = config.blockedInputMessaging || "";
  return out;
}

export const isBlocked = (a: Assessment) => a.blocked;

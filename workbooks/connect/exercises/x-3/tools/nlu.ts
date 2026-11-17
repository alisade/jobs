// Offline, deterministic stand-in for Amazon Lex V2 intent classification over an exported bot
// (Lex JSON export layout). It is NOT Lex: it exists so the exercise can be graded offline.
// Treat it as the environment, not the suspect.
//
// Model (documented so you can reason about it):
// - Each sample utterance is compared with the input by token overlap (F1 over content words).
// - A {Slot} placeholder matches when a value or synonym of the slot's custom slot type occurs in
//   the input as a phrase; the phrase then counts as one matched token.
// - An utterance with a slot placeholder whose value is NOT recognized in the input is penalized
//   (score x 0.5): Lex leans on slot values to classify utterances that contain slots.
// - Intent confidence = best utterance score. Below the locale's nluConfidenceThreshold the result
//   is FallbackIntent (Lex shows no score for the fallback intent).
// - Slot resolution: TOP_RESOLUTION returns the slot type value (sampleValue.value) of the matched
//   value or synonym; ORIGINAL_VALUE returns what the user said.
import * as fs from "fs";
import * as path from "path";

export interface SlotTypeDef { name: string; values: { value: string; synonyms: string[] }[]; strategy: string }
export interface IntentDef { name: string; utterances: string[]; slots: Record<string, string>; fallback: boolean }
export interface Bot { threshold: number; intents: IntentDef[]; slotTypes: Record<string, SlotTypeDef>; voiceId?: string }
export interface Recognition {
  intent: string;
  confidence: number | null;
  slots: Record<string, { originalValue: string; interpretedValue: string } | null>;
  alternatives: { intent: string; confidence: number }[];
}

const read = (p: string) => JSON.parse(fs.readFileSync(p, "utf8"));
const dirs = (p: string) => (fs.existsSync(p) ? fs.readdirSync(p).filter((d) => fs.statSync(path.join(p, d)).isDirectory()).sort() : []);

/** Load bot/<BotName>/BotLocales/<locale>/ from a Lex V2 JSON export. */
export function loadBot(botDir: string, locale = "en_US"): Bot {
  const loc = path.join(botDir, "BotLocales", locale);
  const bl = read(path.join(loc, "BotLocale.json"));
  const slotTypes: Record<string, SlotTypeDef> = {};
  for (const d of dirs(path.join(loc, "SlotTypes"))) {
    const st = read(path.join(loc, "SlotTypes", d, "SlotType.json"));
    slotTypes[st.name] = {
      name: st.name,
      values: (st.slotTypeValues || []).map((v: any) => ({ value: v.sampleValue.value, synonyms: (v.synonyms || []).map((s: any) => s.value) })),
      strategy: (st.valueSelectionSetting && st.valueSelectionSetting.resolutionStrategy) || "ORIGINAL_VALUE",
    };
  }
  const intents: IntentDef[] = [];
  for (const d of dirs(path.join(loc, "Intents"))) {
    const it = read(path.join(loc, "Intents", d, "Intent.json"));
    const slots: Record<string, string> = {};
    for (const s of dirs(path.join(loc, "Intents", d, "Slots"))) {
      const sj = read(path.join(loc, "Intents", d, "Slots", s, "Slot.json"));
      slots[sj.name] = sj.slotTypeName;
    }
    intents.push({ name: it.name, utterances: (it.sampleUtterances || []).map((u: any) => u.utterance), slots, fallback: it.parentIntentSignature === "AMAZON.FallbackIntent" });
  }
  return { threshold: Number(bl.nluConfidenceThreshold), intents, slotTypes, voiceId: bl.voiceSettings && bl.voiceSettings.voiceId };
}

const STOP = new Set("a an the i i'm im me to for of is it on in at and or with this that be am are was please can could you".split(" "));
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9{}' -]+/g, " ").replace(/\s+/g, " ").trim();
const toks = (s: string) => norm(s).split(" ").map((w) => w.replace(/'/g, "")).filter((w) => w && !STOP.has(w));

function findSlotValue(st: SlotTypeDef | undefined, input: string): { phrase: string; value: string } | null {
  if (!st) return null;
  const text = ` ${norm(input)} `;
  let best: { phrase: string; value: string } | null = null;
  for (const v of st.values) {
    for (const p of [v.value, ...v.synonyms]) {
      const np = norm(p);
      if (np && text.includes(` ${np} `) && (!best || np.length > best.phrase.length)) best = { phrase: np, value: v.value };
    }
  }
  return best;
}

function scoreUtterance(bot: Bot, intent: IntentDef, utt: string, input: string) {
  let inputText = norm(input);
  const slotHits: Record<string, { phrase: string; value: string } | null> = {};
  let uttText = norm(utt);
  let missingSlot = false;
  for (const m of utt.match(/\{([A-Za-z0-9_]+)\}/g) || []) {
    const slot = m.slice(1, -1);
    const hit = findSlotValue(bot.slotTypes[intent.slots[slot]], input);
    slotHits[slot] = hit;
    if (hit) inputText = ` ${inputText} `.replace(` ${hit.phrase} `, ` slot${slot.toLowerCase()} `).trim();
    else missingSlot = true;
    uttText = uttText.replace(`{${slot.toLowerCase()}}`, `slot${slot.toLowerCase()}`);
  }
  const a = toks(inputText);
  const b = toks(uttText);
  const setB = new Set(b);
  const overlap = a.filter((w) => setB.has(w)).length;
  const f1 = overlap === 0 ? 0 : (2 * (overlap / a.length) * (overlap / b.length)) / (overlap / a.length + overlap / b.length);
  return { score: Math.round((missingSlot ? f1 * 0.5 : f1) * 100) / 100, slotHits };
}

export function recognize(bot: Bot, input: string): Recognition {
  const scored = bot.intents.filter((i) => !i.fallback).map((intent) => {
    let best = { score: 0, slotHits: {} as Record<string, { phrase: string; value: string } | null> };
    for (const u of intent.utterances) {
      const s = scoreUtterance(bot, intent, u, input);
      if (s.score > best.score) best = s;
    }
    if (!Object.keys(best.slotHits).length) {
      for (const slot of Object.keys(intent.slots)) best.slotHits[slot] = findSlotValue(bot.slotTypes[intent.slots[slot]], input);
    }
    return { intent, ...best };
  }).sort((x, y) => y.score - x.score);
  const top = scored[0];
  const alternatives = scored.slice(0, 3).map((s) => ({ intent: s.intent.name, confidence: s.score }));
  if (!top || top.score < bot.threshold) return { intent: "FallbackIntent", confidence: null, slots: {}, alternatives };
  const slots: Recognition["slots"] = {};
  for (const [slot, type] of Object.entries(top.intent.slots)) {
    const hit = top.slotHits[slot];
    const st = bot.slotTypes[type];
    slots[slot] = hit ? { originalValue: hit.phrase, interpretedValue: st && st.strategy === "TOP_RESOLUTION" ? hit.value : hit.phrase } : null;
  }
  return { intent: top.intent.name, confidence: top.score, slots, alternatives };
}

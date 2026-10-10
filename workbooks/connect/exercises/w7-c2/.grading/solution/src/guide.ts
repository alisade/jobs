// Pick the guided-resolution checklist for the bot's intent.
export type Step = { id: string; text: string; required: boolean; autoWhenVerified?: boolean };
export type Guide = { title: string; steps: Step[] };
export type GuideBook = Record<string, Guide>;

export function guideFor(book: GuideBook, intent: string | undefined): Guide {
  return (intent && book[intent]) || book._default;
}

/** Steps pre-checked from context: identity already verified by the bot/portal handoff. */
export function initialChecks(guide: Guide, callerVerified: boolean): Record<string, boolean> {
  const out: Record<string, boolean> = {};
  for (const s of guide.steps) out[s.id] = !!(s.autoWhenVerified && callerVerified);
  return out;
}

export function canResolve(guide: Guide, checks: Record<string, boolean>): boolean {
  return guide.steps.every((s) => !s.required || checks[s.id]);
}

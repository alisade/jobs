// Pick the guided-resolution checklist for the bot's intent.
export type Step = { id: string; text: string; required: boolean; autoWhenVerified?: boolean };
export type Guide = { title: string; steps: Step[] };
export type GuideBook = Record<string, Guide>;

export function guideFor(book: GuideBook, intent: string | undefined): Guide {
  return book[intent as string]; // TODO: unknown or missing intent
}

export function initialChecks(guide: Guide, _callerVerified: boolean): Record<string, boolean> {
  return Object.fromEntries(guide.steps.map((s) => [s.id, false])); // TODO
}

export function canResolve(_guide: Guide, _checks: Record<string, boolean>): boolean {
  return true; // TODO
}

/**
 * Keeps the tutor from showing the answer of the quiz the learner is on, even if the model says it.
 *
 * push(text) receives streamed tokens and returns what is safe to show now; flush() returns the
 * rest at the end of the stream. Any case-insensitive occurrence of a secret is replaced with
 * WITHHELD.
 *
 * TODO(w2-c1): the prototype checks each token on its own, so "memory" + " cells" slips through.
 */
export const WITHHELD = "[hint withheld]";

export interface LeakGuard {
  push(text: string): string;
  flush(): string;
  readonly leaked: boolean;
}

export function createLeakGuard(secrets: string[]): LeakGuard {
  let leaked = false;
  const redact = (t: string) => {
    let out = t;
    for (const s of secrets) {
      if (s && out.toLowerCase().includes(s.toLowerCase())) {
        out = out.split(s).join(WITHHELD);
        leaked = true;
      }
    }
    return out;
  };
  return {
    push: (text) => redact(text),
    flush: () => "",
    get leaked() { return leaked; },
  };
}

/**
 * Keeps the tutor from showing the answer of the quiz the learner is on, even if the model says it.
 * Streams safely: holds back the last (longest secret - 1) characters, because a secret can
 * straddle tokens, and only releases text that can no longer become part of a match.
 */
export const WITHHELD = "[hint withheld]";

export interface LeakGuard {
  push(text: string): string;
  flush(): string;
  readonly leaked: boolean;
}

export function createLeakGuard(secrets: string[]): LeakGuard {
  const keys = secrets.map((s) => s.trim().toLowerCase()).filter((s) => s.length > 0);
  const hold = keys.reduce((m, k) => Math.max(m, k.length), 0) - 1;
  let pending = "";
  let leaked = false;

  const redactAll = (t: string): string => {
    let out = t;
    for (const k of keys) {
      let i: number;
      while ((i = out.toLowerCase().indexOf(k)) >= 0) {
        out = out.slice(0, i) + WITHHELD + out.slice(i + k.length);
        leaked = true;
      }
    }
    return out;
  };

  return {
    push(text: string): string {
      if (keys.length === 0) return text;
      pending = redactAll(pending + text);
      if (pending.length <= hold) return "";
      // never cut inside an inserted marker
      let cutAt = pending.length - hold;
      const m = pending.lastIndexOf(WITHHELD, cutAt);
      if (m >= 0 && m < cutAt && m + WITHHELD.length > cutAt) cutAt = m + WITHHELD.length;
      const out = pending.slice(0, cutAt);
      pending = pending.slice(cutAt);
      return out;
    },
    flush(): string {
      const out = redactAll(pending);
      pending = "";
      return out;
    },
    get leaked() { return leaked; },
  };
}

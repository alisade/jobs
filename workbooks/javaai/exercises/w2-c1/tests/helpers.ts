import { Subject } from "rxjs";

const enc = new TextEncoder();

export function sse(event: string, data?: unknown): string {
  return `event: ${event}\n` + (data === undefined ? "" : `data: ${JSON.stringify(data)}\n`) + "\n";
}

export function bytes(s: string): Uint8Array {
  return enc.encode(s);
}

/** Split a byte array into chunks at the given byte offsets (to cut events and characters anywhere). */
export function cut(b: Uint8Array, at: number[]): Uint8Array[] {
  const out: Uint8Array[] = [];
  let prev = 0;
  for (const i of [...at, b.length]) {
    out.push(b.slice(prev, i));
    prev = i;
  }
  return out.filter((c) => c.length > 0);
}

/** A fake TutorApi: each stream() call gets its own Subject the test drives. */
export class FakeApi {
  calls: { question: string; lessonId: string; body: Subject<Uint8Array>; unsubscribed: boolean }[] = [];
  stream(question: string, lessonId: string) {
    const body = new Subject<Uint8Array>();
    const rec = { question, lessonId, body, unsubscribed: false };
    this.calls.push(rec);
    return new (require("rxjs").Observable)((sub: any) => {
      const s = body.subscribe(sub);
      return () => { rec.unsubscribed = true; s.unsubscribe(); };
    });
  }
}

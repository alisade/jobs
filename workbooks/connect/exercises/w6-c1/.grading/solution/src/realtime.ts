import { normalize } from "./analysis";
import { CompliancePolicy, RealtimeAlert, SegmentEvent } from "./types";

interface State { seen: Set<string>; negRun: number; alerted: Set<string>; done: boolean }

/**
 * Consumes real-time segment stream events (one Kinesis record each) and raises supervisor alerts:
 *  - ESCALATION_LANGUAGE: a final CUSTOMER Transcript segment contains an escalation phrase
 *  - SUSTAINED_NEGATIVE: N consecutive final CUSTOMER Transcript segments are NEGATIVE
 * Each alert type fires at most once per contact. Utterance (partial) segments never trigger
 * alerts. Kinesis is at-least-once, so a Transcript id seen before is ignored. Events after
 * COMPLETED (or FAILED) for a contact are ignored.
 */
export class RealtimeMonitor {
  private contacts = new Map<string, State>();
  constructor(private policy: CompliancePolicy) {}

  private state(id: string): State {
    let s = this.contacts.get(id);
    if (!s) {
      s = { seen: new Set(), negRun: 0, alerted: new Set(), done: false };
      this.contacts.set(id, s);
    }
    return s;
  }

  handle(ev: SegmentEvent): RealtimeAlert[] {
    const s = this.state(ev.ContactId);
    if (s.done) return [];
    if (ev.EventType === "COMPLETED" || ev.EventType === "FAILED") {
      s.done = true;
      return [];
    }
    if (ev.EventType !== "SEGMENTS") return [];
    const alerts: RealtimeAlert[] = [];
    const phrases = this.policy.escalationLanguage.phrases.map(normalize);
    for (const seg of ev.Segments || []) {
      const t = seg.Transcript;
      if (!t || s.seen.has(t.Id)) continue;
      s.seen.add(t.Id);
      if (t.ParticipantRole !== "CUSTOMER") continue;
      const fire = (type: RealtimeAlert["type"]) => {
        if (s.alerted.has(type)) return;
        s.alerted.add(type);
        alerts.push({ contactId: ev.ContactId, type, atMillis: t.BeginOffsetMillis, transcriptId: t.Id });
      };
      if (phrases.some((p) => normalize(t.Content).includes(p))) fire("ESCALATION_LANGUAGE");
      s.negRun = t.Sentiment === "NEGATIVE" ? s.negRun + 1 : 0;
      if (s.negRun >= this.policy.realtime.sustainedNegativeTurns) fire("SUSTAINED_NEGATIVE");
    }
    return alerts;
  }

  /** Contacts currently being tracked (not COMPLETED/FAILED). */
  active(): string[] {
    return [...this.contacts].filter(([, s]) => !s.done).map(([id]) => id);
  }
}

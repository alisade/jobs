import { normalize } from "./analysis";
import { CompliancePolicy, RealtimeAlert, SegmentEvent } from "./types";

/**
 * Consumes real-time segment stream events (one Kinesis record each) and raises supervisor alerts.
 * TODO: implement per README "Real-time alerts":
 *  - ESCALATION_LANGUAGE on a final CUSTOMER Transcript segment containing an escalation phrase
 *  - SUSTAINED_NEGATIVE after N consecutive NEGATIVE final CUSTOMER Transcript segments
 *  - each alert type at most once per contact; Utterance (partial) segments never alert
 *  - Kinesis is at-least-once: ignore a Transcript id already seen
 *  - ignore everything for a contact after COMPLETED or FAILED
 */
export class RealtimeMonitor {
  constructor(private policy: CompliancePolicy) {}

  handle(ev: SegmentEvent): RealtimeAlert[] {
    void normalize;
    throw new Error(`TODO: handle ${ev.EventType} for ${ev.ContactId} (${this.policy.policyVersion})`);
  }

  /** Contacts currently being tracked (not COMPLETED/FAILED). */
  active(): string[] {
    throw new Error("TODO: active");
  }
}

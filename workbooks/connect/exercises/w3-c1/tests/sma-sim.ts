// A small stand-in for the SIP media application runtime, used by the tests. It drives the
// handler the way the PSTN audio service does: it sends an invocation event, validates the
// response contract, "executes" the returned actions against a scripted caller, and builds the
// next event (Sequence + 1, TransactionAttributes echoed back, ActionData of the last action).
// It models only what the hotline uses; it is not the Chime SDK runtime.
import { Action, PstnEvent, PstnResponse, Participant } from "../src/types";

export type Script = {
  /** digits the caller enters for each PlayAudioAndGetDigits, in order; null = no valid input (action fails) */
  digits?: (string | null)[];
  /** outcome of each CallAndBridge, in order */
  bridges?: ("answer" | "noanswer")[];
  /** after this many successful bridges, who hangs up first */
  hangupAfterBridge?: "LEG-A" | "LEG-B";
  sipHeaders?: Record<string, string>;
  startTimeMs?: number;
  transactionId?: string;
  from?: string;
};

export const HOTLINE = "+18885550177";
const E164 = /^\+[1-9]\d{6,14}$/;
const KNOWN = new Set(["PlayAudio", "PlayAudioAndGetDigits", "CallAndBridge", "Hangup", "Pause", "Speak", "SpeakAndGetDigits", "ReceiveDigits", "SendDigits", "RecordAudio"]);

export function contractErrors(r: PstnResponse, participants: Participant[]): string[] {
  const errs: string[] = [];
  if (!r || r.SchemaVersion !== "1.0") errs.push("SchemaVersion must be \"1.0\"");
  if (!Array.isArray(r?.Actions)) errs.push("Actions must be an array");
  if ((r?.Actions || []).length > 10) errs.push("at most 10 actions per response");
  const ta = r?.TransactionAttributes;
  if (ta !== undefined) {
    if (Object.keys(ta).length > 100) errs.push("TransactionAttributes: at most 100 keys");
    if (JSON.stringify(ta).length > 20 * 1024) errs.push("TransactionAttributes: at most 20 KB");
    for (const [k, v] of Object.entries(ta)) if (typeof v !== "string") errs.push(`TransactionAttributes.${k} must be a string`);
  }
  for (const a of r?.Actions || []) {
    const p = a.Parameters || {};
    if (!KNOWN.has(a.Type)) errs.push(`unknown action ${a.Type}`);
    const s3ok = (s: any) => s && s.Type === "S3" && s.BucketName && s.Key;
    if (a.Type === "PlayAudio" && !s3ok(p.AudioSource)) errs.push("PlayAudio needs AudioSource {Type S3, BucketName, Key}");
    if (a.Type === "PlayAudioAndGetDigits") {
      if (!s3ok(p.AudioSource) || !s3ok(p.FailureAudioSource)) errs.push("PlayAudioAndGetDigits needs AudioSource and FailureAudioSource");
      if (typeof p.RepeatDurationInMilliseconds !== "number") errs.push("PlayAudioAndGetDigits needs RepeatDurationInMilliseconds");
    }
    if (a.Type === "CallAndBridge") {
      if (!E164.test(p.CallerIdNumber || "")) errs.push("CallAndBridge needs an E.164 CallerIdNumber");
      const ep = (p.Endpoints || [])[0];
      if (!ep || ep.BridgeEndpointType !== "PSTN" || !E164.test(ep.Uri || "")) errs.push("CallAndBridge needs Endpoints[0] {BridgeEndpointType PSTN, Uri E.164}");
    }
    if (["PlayAudio", "PlayAudioAndGetDigits", "Hangup"].includes(a.Type)) {
      const target = participants.find((x) => (p.CallId && x.CallId === p.CallId) || (!p.CallId && x.ParticipantTag === p.ParticipantTag));
      if (!target) errs.push(`${a.Type} targets an unknown call leg`);
      else if (target.Status !== "Connected") errs.push(`${a.Type} targets a disconnected leg ${target.ParticipantTag}`);
    }
  }
  return errs;
}

export function newInboundEvent(s: Script = {}): PstnEvent {
  const a: Participant = {
    CallId: `a-${s.transactionId || "tx-1"}`,
    ParticipantTag: "LEG-A",
    To: HOTLINE,
    From: s.from || "+16175550123",
    Direction: "Inbound",
    StartTimeInMilliseconds: String(s.startTimeMs ?? Date.UTC(2026, 9, 7, 2, 14, 0)), // Tue 2026-10-06 22:14 New York
    Status: "Connected",
  };
  if (s.sipHeaders) a.SipHeaders = s.sipHeaders;
  return {
    SchemaVersion: "1.0",
    Sequence: 1,
    InvocationEventType: "NEW_INBOUND_CALL",
    CallDetails: {
      TransactionId: s.transactionId || "tx-1",
      AwsAccountId: "111122223333",
      AwsRegion: "us-east-1",
      SipMediaApplicationId: "5d1c0a4e-7b2f-4c11-9e55-0a9c3f1d2b77",
      Participants: [a],
    },
  };
}

export type Step = { event: PstnEvent; response: PstnResponse };
export type CallResult = { steps: Step[]; errors: string[]; bridged: string[]; played: string[]; ended: boolean; attrs: Record<string, string> };

type Handler = (e: PstnEvent) => Promise<PstnResponse>;

/** Run one whole call through the handler. */
export async function runCall(handler: Handler, s: Script = {}, maxSteps = 40): Promise<CallResult> {
  const digits = [...(s.digits || [])];
  const bridges = [...(s.bridges || [])];
  const steps: Step[] = [];
  const errors: string[] = [];
  const bridged: string[] = [];
  const played: string[] = [];
  let event: PstnEvent | null = newInboundEvent(s);
  let attrs: Record<string, string> = {};
  let ended = false;
  let answered = 0;
  while (event && steps.length < maxSteps) {
    const response = await handler(JSON.parse(JSON.stringify(event)));
    steps.push({ event, response });
    const parts = event.CallDetails.Participants.map((p) => ({ ...p }));
    const errs = contractErrors(response, parts);
    if (errs.length) { errors.push(...errs.map((e) => `seq ${event!.Sequence}: ${e}`)); break; }
    if (response.TransactionAttributes !== undefined) attrs = { ...response.TransactionAttributes };
    const next = (type: PstnEvent["InvocationEventType"], data?: any): PstnEvent => ({
      SchemaVersion: "1.0",
      Sequence: event!.Sequence + 1,
      InvocationEventType: type,
      ...(data ? { ActionData: data } : {}),
      CallDetails: { ...event!.CallDetails, Participants: parts, TransactionAttributes: { ...attrs } },
    });
    let nextEvent: PstnEvent | null = null;
    let last: Action | null = null;
    let failed = false;
    for (const act of response.Actions) {
      last = act;
      const p = act.Parameters;
      if (act.Type === "PlayAudio") { played.push(p.AudioSource.Key); continue; }
      if (act.Type === "PlayAudioAndGetDigits") {
        played.push(p.AudioSource.Key);
        const d = digits.length ? digits.shift()! : null;
        if (d === null || !new RegExp(p.InputDigitsRegex || ".*").test(d)) {
          nextEvent = next("ACTION_FAILED", { Type: act.Type, Parameters: p, ErrorType: "InvalidDigitsReceived", ErrorMessage: "No valid digits" });
          failed = true; break;
        }
        nextEvent = next("ACTION_SUCCESSFUL", { Type: act.Type, Parameters: p, ReceivedDigits: d });
        break; // the service waits for input before running anything after this action
      }
      if (act.Type === "CallAndBridge") {
        const uri = p.Endpoints[0].Uri;
        bridged.push(uri);
        const outcome = bridges.length ? bridges.shift()! : "answer";
        if (outcome === "noanswer") {
          nextEvent = next("ACTION_FAILED", { Type: act.Type, Parameters: p, ErrorType: "CallNotAnswered", ErrorMessage: "Call was not answered" });
          failed = true; break;
        }
        answered++;
        parts.push({ CallId: `b-${event.CallDetails.TransactionId}-${answered}`, ParticipantTag: "LEG-B", To: uri, From: p.CallerIdNumber, Direction: "Outbound", StartTimeInMilliseconds: String(Number(parts[0].StartTimeInMilliseconds) + 30000), Status: "Connected" });
        nextEvent = next("ACTION_SUCCESSFUL", { Type: act.Type, Parameters: p });
        break;
      }
      if (act.Type === "Hangup") {
        const t = parts.find((x) => x.CallId === p.CallId) || parts.find((x) => x.ParticipantTag === p.ParticipantTag)!;
        t.Status = "Disconnected";
        continue;
      }
    }
    if (!failed && last && last.Type === "CallAndBridge" && nextEvent && s.hangupAfterBridge) {
      // deliver the bridge success, then the scripted hangup on the following turn
      const bridgeOk = nextEvent;
      const r2 = await handler(JSON.parse(JSON.stringify(bridgeOk)));
      steps.push({ event: bridgeOk, response: r2 });
      const e2 = contractErrors(r2, bridgeOk.CallDetails.Participants);
      if (e2.length) { errors.push(...e2.map((e) => `seq ${bridgeOk.Sequence}: ${e}`)); break; }
      if (r2.TransactionAttributes !== undefined) attrs = { ...r2.TransactionAttributes };
      const who = s.hangupAfterBridge;
      const parts2 = bridgeOk.CallDetails.Participants.map((x) => ({ ...x }));
      const leaving = parts2.filter((x) => x.ParticipantTag === who && x.Status === "Connected").pop()!;
      leaving.Status = "Disconnected";
      nextEvent = {
        SchemaVersion: "1.0", Sequence: bridgeOk.Sequence + 1, InvocationEventType: "HANGUP",
        ActionData: { Type: "Hangup", Parameters: { SipResponseCode: "0", CallId: leaving.CallId, ParticipantTag: who } },
        CallDetails: { ...bridgeOk.CallDetails, Participants: parts2, TransactionAttributes: { ...attrs } },
      };
      s = { ...s, hangupAfterBridge: undefined };
    }
    if (!nextEvent) {
      if (parts.every((x) => x.Status === "Disconnected")) { ended = true; break; }
      if (!response.Actions.length) break; // call idles (bridged, or waiting)
      const lastAct = response.Actions[response.Actions.length - 1];
      nextEvent = next("ACTION_SUCCESSFUL", { Type: lastAct.Type, Parameters: lastAct.Parameters });
    }
    event = nextEvent;
  }
  return { steps, errors, bridged, played, ended, attrs };
}

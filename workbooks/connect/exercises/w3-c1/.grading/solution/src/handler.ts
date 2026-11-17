// LFG IT On-Call Hotline - SIP media application handler (PSTN audio, Amazon Chime SDK).
// Every invocation is answered from the event alone: the call's state lives in
// TransactionAttributes, never in module scope, because one warm Lambda container serves many
// concurrent calls and the service retries an invocation that is slow to answer.
import { Action, Participant, PstnEvent, PstnResponse } from "./types";
import { PROMPTS } from "./prompts";
import { onCallAt, roster } from "./roster";

type State = "COLLECT_ID" | "MENU" | "BRIDGE_PRIMARY" | "BRIDGE_SECONDARY" | "BRIDGE_HELPDESK" | "CONNECTED" | "ENDING";

const respond = (Actions: Action[], TransactionAttributes?: Record<string, string>): PstnResponse =>
  TransactionAttributes ? { SchemaVersion: "1.0", Actions, TransactionAttributes } : { SchemaVersion: "1.0", Actions };

const leg = (e: PstnEvent, tag: "LEG-A" | "LEG-B"): Participant | undefined =>
  e.CallDetails.Participants.find((p) => p.ParticipantTag === tag);

function header(p: Participant | undefined, name: string): string | undefined {
  const h = p?.SipHeaders || {};
  const k = Object.keys(h).find((x) => x.toLowerCase() === name.toLowerCase());
  return k ? h[k] : undefined;
}

const collectEmployeeId = (a: Participant): Action => ({
  Type: "PlayAudioAndGetDigits",
  Parameters: {
    CallId: a.CallId,
    ParticipantTag: "LEG-A",
    InputDigitsRegex: "^\\d{6}$",
    AudioSource: PROMPTS.enterEmployeeId,
    FailureAudioSource: PROMPTS.invalidEntry,
    MinNumberOfDigits: 6,
    MaxNumberOfDigits: 6,
    TerminatorDigits: ["#"],
    InBetweenDigitsDurationInMilliseconds: 5000,
    Repeat: 3,
    RepeatDurationInMilliseconds: 10000,
  },
});

const menu = (a: Participant): Action => ({
  Type: "PlayAudioAndGetDigits",
  Parameters: {
    CallId: a.CallId,
    ParticipantTag: "LEG-A",
    InputDigitsRegex: "^[12]$",
    AudioSource: PROMPTS.menu,
    FailureAudioSource: PROMPTS.invalidEntry,
    MinNumberOfDigits: 1,
    MaxNumberOfDigits: 1,
    Repeat: 2,
    RepeatDurationInMilliseconds: 8000,
  },
});

const play = (a: Participant, AudioSource: object): Action => ({ Type: "PlayAudio", Parameters: { CallId: a.CallId, ParticipantTag: "LEG-A", AudioSource } });

const bridge = (a: Participant, number: string): Action => ({
  Type: "CallAndBridge",
  Parameters: {
    CallTimeoutSeconds: 25,
    CallerIdNumber: a.To || roster.hotlineNumber, // present the hotline DID, not the caller's number
    RingbackTone: PROMPTS.ringback,
    Endpoints: [{ BridgeEndpointType: "PSTN", Uri: number }],
  },
});

const hangup = (p: Participant): Action => ({ Type: "Hangup", Parameters: { CallId: p.CallId, ParticipantTag: p.ParticipantTag, SipResponseCode: "0" } });

const mask = (id?: string) => (id ? `****${id.slice(-2)}` : "");

export const handler = async (event: PstnEvent): Promise<PstnResponse> => {
  const a = leg(event, "LEG-A");
  const b = leg(event, "LEG-B");
  const attrs: Record<string, string> = { ...(event.CallDetails.TransactionAttributes || {}) };
  const state = (attrs.state || "") as State | "";
  const set = (s: State, extra: Record<string, string> = {}) => ({ ...attrs, ...extra, state: s });
  let out: PstnResponse = respond([]);

  if (!a) {
    out = respond([]);
  } else {
    switch (event.InvocationEventType) {
      case "NEW_INBOUND_CALL": {
        const fromAvaya = header(a, "X-Employee-Id");
        out = fromAvaya && /^\d{6}$/.test(fromAvaya)
          ? respond([menu(a)], { state: "MENU", employeeId: fromAvaya, idSource: "sip-header" })
          : respond([collectEmployeeId(a)], { state: "COLLECT_ID" });
        break;
      }
      case "ACTION_SUCCESSFUL": {
        const t = event.ActionData?.Type;
        const digits = (event.ActionData?.ReceivedDigits || "").replace(/#$/, "");
        if (t === "PlayAudioAndGetDigits" && state === "COLLECT_ID") {
          out = respond([menu(a)], set("MENU", { employeeId: digits, idSource: "dtmf" }));
        } else if (t === "PlayAudioAndGetDigits" && state === "MENU" && digits === "1") {
          const oc = onCallAt(Number(a.StartTimeInMilliseconds));
          out = respond([play(a, PROMPTS.connectingOnCall), bridge(a, oc.primary)], set("BRIDGE_PRIMARY", { shift: oc.shift, primary: oc.primary, secondary: oc.secondary }));
        } else if (t === "PlayAudioAndGetDigits" && state === "MENU" && digits === "2") {
          out = respond([bridge(a, roster.helpDeskNumber)], set("BRIDGE_HELPDESK"));
        } else if (t === "CallAndBridge") {
          out = respond([], set("CONNECTED"));
        } else {
          out = respond([]);
        }
        break;
      }
      case "ACTION_FAILED": {
        const t = event.ActionData?.Type;
        if (t === "CallAndBridge" && state === "BRIDGE_PRIMARY") {
          out = respond([bridge(a, attrs.secondary)], set("BRIDGE_SECONDARY"));
        } else if (t === "CallAndBridge" && state === "BRIDGE_SECONDARY") {
          out = respond([play(a, PROMPTS.onCallUnavailable), bridge(a, roster.helpDeskNumber)], set("BRIDGE_HELPDESK"));
        } else {
          out = respond([play(a, PROMPTS.goodbye), hangup(a)], set("ENDING"));
        }
        break;
      }
      case "HANGUP": {
        const tag = event.ActionData?.Parameters?.ParticipantTag;
        if (tag === "LEG-A" && b && b.Status === "Connected") out = respond([hangup(b)], set("ENDING"));
        else if (tag === "LEG-B" && a.Status === "Connected") out = respond([play(a, PROMPTS.engineerLeft), hangup(a)], set("ENDING"));
        else out = respond([]);
        break;
      }
      case "INVALID_LAMBDA_RESPONSE":
        out = respond(a.Status === "Connected" ? [hangup(a)] : []);
        break;
      default:
        out = respond([]);
    }
  }

  console.log(JSON.stringify({
    msg: "sma-invocation",
    transactionId: event.CallDetails.TransactionId,
    sequence: event.Sequence,
    event: event.InvocationEventType,
    stateIn: state,
    stateOut: out.TransactionAttributes?.state ?? state,
    actions: out.Actions.map((x) => x.Type),
    employeeId: mask(out.TransactionAttributes?.employeeId ?? attrs.employeeId),
  }));
  return out;
};

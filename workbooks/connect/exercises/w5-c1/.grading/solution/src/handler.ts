// Reference solution: LFG help desk bot code hook (Lex V2, messageVersion 1.0).
import { Deps, SystemCode } from "./deps";
import { Intent, LexEvent, LexResponse, Message, SlotValue, Slots } from "./lex-types";

const SYSTEM_LABEL: Record<SystemCode, string> = {
  EMAIL: "email",
  VPN: "VPN",
  SAP: "SAP",
  SAP_CONCUR: "SAP Concur",
  WORKDAY: "Workday",
};
const MAX_ID_ATTEMPTS = 2;
const MAX_FALLBACKS = 2;

type Attrs = Record<string, string>;
const text = (content: string): Message[] => [{ contentType: "PlainText", content }];

function slotText(s: SlotValue | null | undefined): string | undefined {
  return s?.value?.interpretedValue ?? s?.value?.originalValue ?? undefined;
}
function setSlot(slots: Slots, name: string, value: string): void {
  slots[name] = { shape: "Scalar", value: { originalValue: value, interpretedValue: value, resolvedValues: [value] } };
}
export function normalizeEmployeeId(raw: string | undefined): string | null {
  if (!raw) return null;
  const s = raw.trim().toUpperCase().replace(/^E[\s-]*/, "").replace(/[\s-]/g, "");
  return /^\d{5}$/.test(s) ? s : null;
}
function slotSummary(slots: Slots): string {
  const out: Record<string, string> = {};
  for (const [k, v] of Object.entries(slots)) {
    const t = slotText(v);
    if (t !== undefined) out[k] = t;
  }
  return JSON.stringify(out);
}

function handoff(intent: Intent, attrs: Attrs, reason: string, queue: string, summary: string, message: string, state: "Failed" | "Fulfilled" = "Failed"): LexResponse {
  const slots = intent.slots || {};
  return {
    sessionState: {
      sessionAttributes: {
        ...attrs,
        handoff: "true",
        handoffReason: reason,
        handoffQueue: queue,
        intent: intent.name,
        slots: slotSummary(slots),
        summary: summary.slice(0, 300),
      },
      dialogAction: { type: "Close" },
      intent: { name: intent.name, state, slots },
    },
    messages: text(message),
  };
}
function close(intent: Intent, attrs: Attrs, message: string): LexResponse {
  return {
    sessionState: { sessionAttributes: { ...attrs, handoff: "false" }, dialogAction: { type: "Close" }, intent: { name: intent.name, state: "Fulfilled", slots: intent.slots || {} } },
    messages: text(message),
  };
}
function elicit(intent: Intent, attrs: Attrs, slot: string, message: string): LexResponse {
  return {
    sessionState: { sessionAttributes: attrs, dialogAction: { type: "ElicitSlot", slotToElicit: slot }, intent: { name: intent.name, state: "InProgress", confirmationState: "None", slots: intent.slots || {} } },
    messages: text(message),
  };
}
function delegate(intent: Intent, attrs: Attrs): LexResponse {
  return { sessionState: { sessionAttributes: attrs, dialogAction: { type: "Delegate" }, intent: { name: intent.name, state: "InProgress", confirmationState: intent.confirmationState || "None", slots: intent.slots || {} } } };
}

/** Validate (or prefill) EmployeeId. Returns a response to send, or null when the slot is good. */
async function checkEmployeeId(intent: Intent, attrs: Attrs, deps: Deps): Promise<LexResponse | null> {
  const slots = (intent.slots = { ...(intent.slots || {}) });
  if (!slots.EmployeeId && attrs.callerVerified === "true" && normalizeEmployeeId(attrs.employeeId)) {
    setSlot(slots, "EmployeeId", normalizeEmployeeId(attrs.employeeId)!);
  }
  if (!slots.EmployeeId) {
    return elicit(intent, attrs, "EmployeeId", "Please say or enter your five digit employee ID.");
  }
  const id = normalizeEmployeeId(slotText(slots.EmployeeId));
  const record = id ? await deps.directory.lookup(id) : null;
  if (!id || !record) {
    const attempts = Number(attrs.employeeIdAttempts || "0") + 1;
    attrs.employeeIdAttempts = String(attempts);
    slots.EmployeeId = null;
    if (attempts >= MAX_ID_ATTEMPTS) {
      return handoff(intent, attrs, id ? "EMPLOYEE_NOT_FOUND" : "EMPLOYEE_ID_INVALID", "GeneralSupport",
        `${intent.name}: caller could not provide a valid employee ID after ${attempts} attempts`,
        "Let me connect you with a service desk analyst who can help.");
    }
    return elicit(intent, attrs, "EmployeeId", id
      ? "I could not find that employee ID. Please say or enter your five digit employee ID again."
      : "That did not sound like a five digit employee ID. Please say or enter it again.");
  }
  setSlot(slots, "EmployeeId", id);
  attrs.employeeId = id;
  return null;
}

async function resetDialog(intent: Intent, attrs: Attrs, deps: Deps): Promise<LexResponse> {
  const early = await checkEmployeeId(intent, attrs, deps);
  if (early) return early;
  const slots = intent.slots!;
  const sys = slots.SystemName;
  if (!sys) return elicit(intent, attrs, "SystemName", "Which system do you need a reset for: email, VPN, SAP, Concur or Workday?");
  const resolved = (sys.value?.resolvedValues || []).filter((v): v is SystemCode => v in SYSTEM_LABEL);
  if (resolved.length !== 1) {
    slots.SystemName = null;
    const msg = resolved.length > 1
      ? `Did you mean ${resolved.map((r) => SYSTEM_LABEL[r]).join(" or ")}?`
      : "I can reset email, VPN, SAP, Concur or Workday passwords. Which one do you need?";
    return elicit(intent, attrs, "SystemName", msg);
  }
  setSlot(slots, "SystemName", resolved[0]);
  if (intent.confirmationState === "Denied") {
    slots.SystemName = null;
    return elicit(intent, attrs, "SystemName", "No problem. Which system should I reset instead?");
  }
  if (intent.confirmationState === "Confirmed") return delegate(intent, attrs);
  return {
    sessionState: { sessionAttributes: attrs, dialogAction: { type: "ConfirmIntent" }, intent: { name: intent.name, state: "InProgress", confirmationState: "None", slots } },
    messages: text(`To confirm, you want to reset your ${SYSTEM_LABEL[resolved[0]]} password and get a link on your registered device?`),
  };
}

async function resetFulfill(intent: Intent, attrs: Attrs, deps: Deps): Promise<LexResponse> {
  const slots = intent.slots || {};
  const id = normalizeEmployeeId(slotText(slots.EmployeeId))!;
  const system = ((slots.SystemName?.value?.resolvedValues || [])[0] || slotText(slots.SystemName)) as SystemCode;
  const label = SYSTEM_LABEL[system] || system;
  const result = await deps.reset.sendResetLink(id, system);
  if (result === "SENT") return close(intent, attrs, `Done. A ${label} reset link is on its way to your registered device.`);
  const reason = result === "NO_MFA" ? "NO_MFA" : "RESET_FAILED";
  return handoff(intent, attrs, reason, "PasswordReset",
    `ResetPassword ${label} for employee ${id}: ${result === "NO_MFA" ? "no MFA device enrolled, needs identity proofing" : "reset service failed"}`,
    "I could not complete the reset automatically. I will connect you with a password reset specialist.");
}

async function unlockFulfill(intent: Intent, attrs: Attrs, deps: Deps): Promise<LexResponse> {
  const id = normalizeEmployeeId(slotText((intent.slots || {}).EmployeeId))!;
  const rec = await deps.directory.lookup(id);
  if (!rec) return handoff(intent, attrs, "EMPLOYEE_NOT_FOUND", "GeneralSupport", `UnlockAccount: employee ${id} not found`, "Let me connect you with a service desk analyst.");
  if (rec.status === "DISABLED") {
    return handoff(intent, attrs, "ACCOUNT_DISABLED", "Security", `UnlockAccount for employee ${id}: account is DISABLED, security review needed`,
      "Your account needs a security review. I will connect you with the access team.");
  }
  const r = await deps.directory.unlock(id);
  if (r === "UNLOCKED") return close(intent, attrs, "Your account is unlocked. You can sign in again now.");
  if (r === "NOT_LOCKED") return close(intent, attrs, "Your account is not locked. If you forgot your password, say reset my password.");
  return handoff(intent, attrs, "UNLOCK_FAILED", "GeneralSupport", `UnlockAccount for employee ${id}: unlock failed`, "I could not unlock your account. Let me connect you with an analyst.");
}

function outageFulfill(intent: Intent, attrs: Attrs): LexResponse {
  const slots = intent.slots || {};
  const service = (slots.ServiceName?.value?.resolvedValues || [])[0] || slotText(slots.ServiceName) || "unknown";
  const scope = (slots.Scope?.value?.resolvedValues || [])[0] || slotText(slots.Scope) || "ME";
  const many = scope === "MANY";
  return handoff(intent, attrs, "OUTAGE_REPORTED", many ? "MajorIncident" : "GeneralSupport",
    `ReportOutage: ${service} affecting ${many ? "multiple people" : "the caller only"}`,
    many ? "Thanks. I am connecting you to the major incident team now." : "Thanks. I am connecting you to an analyst now.", "Fulfilled");
}

function fallback(intent: Intent, attrs: Attrs, transcript: string): LexResponse {
  const count = Number(attrs.fallbackCount || "0") + 1;
  attrs.fallbackCount = String(count);
  if (count >= MAX_FALLBACKS) {
    return handoff({ name: "FallbackIntent", slots: {} }, attrs, "NOT_UNDERSTOOD", "GeneralSupport",
      `Bot could not understand the request after ${count} tries. Last utterance: ${transcript}`.slice(0, 300),
      "Let me connect you with a service desk analyst.");
  }
  return { sessionState: { sessionAttributes: attrs, dialogAction: { type: "ElicitIntent" } }, messages: text("I can help with password resets, account unlocks and outages. What do you need?") };
}

export function createHandler(deps: Deps) {
  return async function handler(event: LexEvent): Promise<LexResponse> {
    const attrs: Attrs = { ...(event.sessionState.sessionAttributes || {}) };
    const intent: Intent = JSON.parse(JSON.stringify(event.sessionState.intent));
    try {
      const dialog = event.invocationSource === "DialogCodeHook";
      switch (intent.name) {
        case "ResetPassword":
          return dialog ? await resetDialog(intent, attrs, deps) : await resetFulfill(intent, attrs, deps);
        case "UnlockAccount":
          if (dialog) return (await checkEmployeeId(intent, attrs, deps)) || delegate(intent, attrs);
          return await unlockFulfill(intent, attrs, deps);
        case "ReportOutage":
          return dialog ? delegate(intent, attrs) : outageFulfill(intent, attrs);
        case "FallbackIntent":
          return fallback(intent, attrs, event.inputTranscript || "");
        default:
          return handoff(intent, attrs, "UNSUPPORTED_INTENT", "GeneralSupport", `Unsupported intent ${intent.name}`, "Let me connect you with a service desk analyst.");
      }
    } catch (err) {
      return handoff(intent, attrs, "BACKEND_ERROR", "GeneralSupport", `${intent.name}: backend error (${String((err as Error).message).slice(0, 80)})`,
        "Something went wrong on our side. Let me connect you with a service desk analyst.");
    }
  };
}

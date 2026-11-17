// LFG IT On-Call Hotline - SIP media application handler (PSTN audio, Amazon Chime SDK).
//
// Inherited code (2023, written for the Avaya-era escalation line). It works in the happy-path
// demo and fails in production; see README.md. Keep the public shape: export `handler`.
import { PstnEvent, PstnResponse } from "./types";
import { PROMPTS } from "./prompts";
import { onCallAt, roster } from "./roster";

// "Remember where each caller is in the menu."
let state = "";
let employeeId = "";

export const handler = async (event: PstnEvent): Promise<PstnResponse> => {
  const legA = event.CallDetails.Participants[0];

  if (event.InvocationEventType === "NEW_INBOUND_CALL") {
    state = "COLLECT_ID";
    return {
      SchemaVersion: "1.0",
      Actions: [{
        Type: "PlayAudioAndGetDigits",
        Parameters: {
          CallId: legA.CallId,
          ParticipantTag: "LEG-A",
          InputDigitsRegex: "^\\d{6}$",
          AudioSource: PROMPTS.enterEmployeeId,
          FailureAudioSource: PROMPTS.invalidEntry,
          MinNumberOfDigits: 6,
          MaxNumberOfDigits: 6,
          Repeat: 3,
          RepeatDurationInMilliseconds: 10000,
        },
      }],
    };
  }

  if (event.InvocationEventType === "ACTION_SUCCESSFUL" && state === "COLLECT_ID") {
    employeeId = event.ActionData?.ReceivedDigits || "";
    state = "MENU";
    return {
      SchemaVersion: "1.0",
      Actions: [{
        Type: "PlayAudioAndGetDigits",
        Parameters: {
          CallId: legA.CallId,
          ParticipantTag: "LEG-A",
          InputDigitsRegex: "^[12]$",
          AudioSource: PROMPTS.menu,
          FailureAudioSource: PROMPTS.invalidEntry,
          MinNumberOfDigits: 1,
          MaxNumberOfDigits: 1,
          Repeat: 2,
          RepeatDurationInMilliseconds: 8000,
        },
      }],
    };
  }

  if (event.InvocationEventType === "ACTION_SUCCESSFUL" && state === "MENU") {
    const digit = event.ActionData?.ReceivedDigits;
    const target = digit === "1" ? onCallAt(Date.now()).primary : roster.helpDeskNumber;
    state = "BRIDGED";
    console.log(`bridging employee ${employeeId} to ${target}`);
    return {
      SchemaVersion: "1.0",
      Actions: [{
        Type: "CallAndBridge",
        Parameters: {
          CallTimeoutSeconds: 25,
          CallerIdNumber: legA.From,
          Endpoints: [{ BridgeEndpointType: "PSTN", Uri: target }],
        },
      }],
    };
  }

  // TODO: ACTION_FAILED (digits and bridge), HANGUP from either leg, INVALID_LAMBDA_RESPONSE,
  //       X-Employee-Id from the Avaya SBC, secondary on-call failover, help desk fallback.
  return { SchemaVersion: "1.0", Actions: [] };
};

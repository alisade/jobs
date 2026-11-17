// Amazon Lex V2 code hook contract (messageVersion 1.0), the fields this exercise uses.
// Source: Lex V2 developer guide, "Interpreting the input event format" and "Response format".
// Parse tolerantly: AWS may add fields without bumping messageVersion.

export type SlotValue = {
  shape?: "Scalar" | "List" | "Composite";
  value?: { originalValue?: string; interpretedValue?: string; resolvedValues?: string[] };
  values?: SlotValue[];
};
export type Slots = Record<string, SlotValue | null>;

export type IntentState = "Failed" | "Fulfilled" | "FulfillmentInProgress" | "InProgress" | "ReadyForFulfillment" | "Waiting";
export type ConfirmationState = "Confirmed" | "Denied" | "None";

export type Intent = { name: string; state?: IntentState; confirmationState?: ConfirmationState; slots?: Slots };

export type LexEvent = {
  messageVersion: string;
  invocationSource: "DialogCodeHook" | "FulfillmentCodeHook";
  inputMode: "DTMF" | "Speech" | "Text";
  responseContentType?: string;
  sessionId: string;
  inputTranscript: string;
  invocationLabel?: string;
  bot: { id: string; name: string; localeId: string; version: string; aliasId?: string; aliasName?: string };
  interpretations: { intent: Intent; nluConfidence?: number; interpretationSource?: string }[];
  proposedNextState?: { dialogAction: { type: string; slotToElicit?: string }; intent: Intent; prompt?: { attempt: string } };
  requestAttributes?: Record<string, string>;
  sessionState: {
    sessionAttributes?: Record<string, string>;
    activeContexts?: unknown[];
    intent: Intent;
    originatingRequestId?: string;
  };
};

export type DialogActionType = "Close" | "ConfirmIntent" | "Delegate" | "ElicitIntent" | "ElicitSlot";
export type Message = { contentType: "PlainText" | "SSML" | "CustomPayload" | "ImageResponseCard"; content?: string };

export type LexResponse = {
  sessionState: {
    sessionAttributes?: Record<string, string>;
    dialogAction: { type: DialogActionType; slotToElicit?: string };
    intent?: Intent;
  };
  messages?: Message[];
  requestAttributes?: Record<string, string>;
};

// The slice of the agent workspace SDK this app uses, as an adapter interface.
//
// In production this is a ContactClient from the Amazon Connect SDK (@amazon-connect/contact,
// constructed with the provider from AmazonConnectApp.init in @amazon-connect/app). The method
// names and event shape below match that package's published typings (v1.0.14): onConnected /
// offConnected / onCleared / offCleared take a handler receiving a lifecycle event, and
// getAttributes(contactId, keys | "*") resolves to Record<string, string>.
// Tests inject a fake (tests/fakeWorkspace.ts), so nothing here talks to a real workspace.

export type ContactLifecycleEvent = {
  contactId: string;
  initialContactId: string | undefined;
  type: string; // "voice" | "chat" | "task" | ...
  subtype: string;
};

export type ContactHandler = (e: ContactLifecycleEvent) => void | Promise<void>;

export interface ContactEventSource {
  onConnected(handler: ContactHandler): void;
  offConnected(handler: ContactHandler): void;
  onCleared(handler: ContactHandler): void;
  offCleared(handler: ContactHandler): void;
  getAttributes(contactId: string, attributes: string[] | "*"): Promise<Record<string, string>>;
}

/** Contact attributes the help desk flow sets before Transfer to queue (see README). */
export const HANDOFF_KEYS = [
  "botSummary",
  "lexIntent",
  "lexSlots",
  "incidentNumber",
  "incidentSysId",
  "callerVerified",
  "vip",
  "channel",
] as const;

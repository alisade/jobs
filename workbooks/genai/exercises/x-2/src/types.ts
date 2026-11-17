// Shared types for the assistant chat page.

export interface Message {
  role: "customer" | "assistant";
  text: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
}

export interface HandoffRequest {
  conversationId: string;
  /** "customer: ..." / "assistant: ..." lines, oldest first */
  transcript: string[];
}

export interface HandoffClient {
  handoff(req: HandoffRequest): Promise<{ ticketId: string }>;
}

/** Keyboard shortcut registry. register() returns an unregister function. */
export interface Shortcuts {
  register(combo: string, fn: () => void): () => void;
}

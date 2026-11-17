// Test helpers: conversations, a fake handoff client, a fake shortcut registry.
import type { Conversation, HandoffClient, HandoffRequest, Shortcuts } from "../src/types";

export const CONVERSATIONS: Conversation[] = [
  {
    id: "c-101",
    title: "Tent for two",
    messages: [
      { role: "customer", text: "Do you have a tent for two under 2 kg?" },
      { role: "assistant", text: "The Ridgeline 2P weighs 1.9 kg." },
    ],
  },
  {
    id: "c-102",
    title: "Return a stove",
    messages: [
      { role: "customer", text: "My camp stove leaks gas, order 1182." },
      { role: "assistant", text: "I am sorry. I can start a return for order 1182." },
      { role: "customer", text: "I want to talk to someone." },
    ],
  },
  {
    id: "c-103",
    title: "Store hours",
    messages: [{ role: "customer", text: "When does the Boulder store open?" }],
  },
];

export function fakeClient() {
  const calls: HandoffRequest[] = [];
  let n = 0;
  const client: HandoffClient = {
    handoff: jest.fn(async (req: HandoffRequest) => {
      calls.push(req);
      n++;
      return { ticketId: `T-${5000 + n}` };
    }),
  };
  return { client, calls };
}

export function fakeShortcuts() {
  const handlers = new Map<number, { combo: string; fn: () => void }>();
  let next = 0;
  const shortcuts: Shortcuts = {
    register: jest.fn((combo: string, fn: () => void) => {
      const id = next++;
      handlers.set(id, { combo, fn });
      return () => {
        handlers.delete(id);
      };
    }),
  };
  return {
    shortcuts,
    fire: (combo: string) => {
      for (const h of Array.from(handlers.values())) if (h.combo === combo) h.fn();
    },
    active: () => handlers.size,
  };
}

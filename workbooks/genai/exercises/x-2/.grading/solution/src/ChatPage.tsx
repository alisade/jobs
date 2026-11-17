// Kestrel "My conversations" page: switch between assistant conversations and hand one to a
// person (button or Alt+H). Release 2026.10.28 added the shortcut (WEB-3302).
import { useCallback, useEffect, useRef, useState } from "react";
import type { Conversation, HandoffClient, Shortcuts } from "./types";
import { windowShortcuts } from "./shortcuts";

export interface ChatPageProps {
  conversations: Conversation[];
  client: HandoffClient;
  shortcuts?: Shortcuts;
}

export function transcriptOf(c: Conversation): string[] {
  return c.messages.map((m) => `${m.role}: ${m.text}`);
}

export function ChatPage({ conversations, client, shortcuts = windowShortcuts }: ChatPageProps) {
  const [activeId, setActiveId] = useState(conversations[0]?.id);
  const [ticket, setTicket] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const active = conversations.find((c) => c.id === activeId);

  // The handler must read the CURRENT conversation. Keep the latest values in a ref so the handler
  // (and the shortcut registration) can stay stable without capturing the first render's values.
  const latest = useRef({ active, client });
  latest.current = { active, client };

  const requestHandoff = useCallback(async () => {
    const { active: conv, client: api } = latest.current;
    if (!conv) return;
    setFailed(false);
    try {
      const res = await api.handoff({ conversationId: conv.id, transcript: transcriptOf(conv) });
      setTicket(res.ticketId);
    } catch {
      setFailed(true);
    }
  }, []);

  useEffect(() => {
    // one registration at a time; the cleanup removes it before any re-registration and on unmount
    return shortcuts.register("alt+h", () => {
      void requestHandoff();
    });
  }, [shortcuts, requestHandoff]);

  return (
    <main>
      <nav aria-label="Conversations">
        {conversations.map((c) => (
          <button
            key={c.id}
            type="button"
            aria-pressed={c.id === activeId}
            onClick={() => {
              setActiveId(c.id);
              setTicket(null);
            }}
          >
            {c.title}
          </button>
        ))}
      </nav>
      {active && (
        <section aria-label="Transcript">
          <h2>{active.title}</h2>
          <ol>
            {active.messages.map((m, i) => (
              <li key={i}>
                <b>{m.role === "customer" ? "You" : "Assistant"}:</b> {m.text}
              </li>
            ))}
          </ol>
        </section>
      )}
      <button type="button" onClick={() => void requestHandoff()}>
        Talk to a person
      </button>
      <p className="small">Shortcut: Alt+H</p>
      {ticket && <p role="status">A person will pick this up. Ticket {ticket}.</p>}
      {failed && <p role="alert">We could not reach a person. Please try again.</p>}
    </main>
  );
}

// Kestrel "My conversations" page: switch between assistant conversations and hand one to a
// person (button or Alt+H). Release 2026.10.28 added the shortcut (WEB-3302).
import { useCallback, useEffect, useState } from "react";
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

  // Stable handler so the Alt+H listener is registered once, not on every render.
  const requestHandoff = useCallback(async () => {
    if (!active) return;
    setFailed(false);
    try {
      const res = await client.handoff({ conversationId: active.id, transcript: transcriptOf(active) });
      setTicket(res.ticketId);
    } catch {
      setFailed(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const off = shortcuts.register("alt+h", () => {
      void requestHandoff();
    });
    return off;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

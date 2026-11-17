// Kestrel storefront assistant panel.
import { useState } from "react";
import { formatPrice } from "./events";
import { useAssistantStream, type OpenStream } from "./useAssistantStream";

export interface AssistantPanelProps {
  openStream: OpenStream;
  onHandoff?: (conversationId: string | null) => void;
}

// TODO (README "UI requirements"): AI disclosure, Stop while streaming, status line,
// error alert with "Try again" when retryable, product cards with price and stock,
// "Talk to a person" handoff, Send disabled while streaming or when the box is empty,
// clear the box after sending.
export function AssistantPanel({ openStream }: AssistantPanelProps) {
  const s = useAssistantStream(openStream);
  const [draft, setDraft] = useState("");

  return (
    <section aria-label="Shopping assistant">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          s.send(draft);
        }}
      >
        <label htmlFor="ka-ask">Ask about products</label>
        <textarea id="ka-ask" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button type="submit">Send</button>
      </form>
      <div role="log" aria-live="polite" aria-label="Assistant answer">{s.text}</div>
      <ul aria-label="Suggested products">
        {s.products.map((p) => (
          <li key={p.sku}>
            {p.name} {formatPrice(p.price_cents)}
          </li>
        ))}
      </ul>
    </section>
  );
}

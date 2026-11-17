// Kestrel storefront assistant panel. Reference solution.
import { useState } from "react";
import { formatPrice } from "./events";
import { useAssistantStream, type OpenStream } from "./useAssistantStream";

export interface AssistantPanelProps {
  openStream: OpenStream;
  onHandoff?: (conversationId: string | null) => void;
}

const STATUS_TEXT: Record<string, string> = {
  streaming: "Assistant is typing",
  stopped: "Stopped",
  done: "",
  idle: "",
  error: "",
};

export function AssistantPanel({ openStream, onHandoff }: AssistantPanelProps) {
  const s = useAssistantStream(openStream);
  const [draft, setDraft] = useState("");
  const streaming = s.status === "streaming";

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (streaming || !draft.trim()) return;
    s.send(draft);
    setDraft("");
  }

  return (
    <section aria-label="Shopping assistant">
      <p className="disclosure">
        You are chatting with Kestrel&apos;s AI assistant. It can make mistakes: check price and stock on the product page.
      </p>
      <form onSubmit={submit}>
        <label htmlFor="ka-ask">Ask about products</label>
        <textarea id="ka-ask" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button type="submit" disabled={streaming || !draft.trim()}>Send</button>
        {streaming && (
          <button type="button" onClick={s.stop}>Stop</button>
        )}
      </form>
      <p role="status">{STATUS_TEXT[s.status]}</p>
      <div role="log" aria-live="polite" aria-label="Assistant answer">{s.text}</div>
      {s.products.length > 0 && (
        <ul aria-label="Suggested products">
          {s.products.map((p) => (
            <li key={p.sku}>
              <article aria-label={p.name}>
                <a href={p.url}>{p.name}</a> <span>{formatPrice(p.price_cents)}</span>{" "}
                <span>{p.in_stock ? "In stock" : "Out of stock"}</span>
              </article>
            </li>
          ))}
        </ul>
      )}
      {s.status === "error" && s.error && (
        <div role="alert">
          {s.error.message}{" "}
          {s.error.retryable && (
            <button type="button" onClick={s.retry}>Try again</button>
          )}
        </div>
      )}
      {onHandoff && (
        <button type="button" onClick={() => onHandoff(s.conversationId ?? null)}>Talk to a person</button>
      )}
    </section>
  );
}

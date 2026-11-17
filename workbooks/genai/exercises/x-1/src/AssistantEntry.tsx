// Storefront search box with the assistant behind a flag.
//
// The spike below handles "off" (legacy search only) and "on" (assistant answer) for a fixed flag
// value. Everything else in README "Requirements" is yours: live flag changes and the kill switch,
// shadow mode, fallback on error and on a slow first token, "Show regular results", the handoff,
// and the analytics events.
import { useState } from "react";
import { LegacyResults, type LegacyResult, type SearchFn } from "./LegacySearch";
import { useAssistantStream, type OpenStream } from "./vendor/useAssistantStream";
import { formatPrice } from "./vendor/events";
import { modeFor, type AnalyticsEvent, type FlagClient } from "./rollout";

export interface AssistantEntryProps {
  userId: string;
  flags: FlagClient;
  openStream: OpenStream;
  search: SearchFn;
  track: (e: AnalyticsEvent) => void;
  onHandoff?: (conversationId: string | null) => void;
  /** fall back to legacy results when no token arrives within this budget */
  ttftBudgetMs?: number;
}

export const FALLBACK_NOTICE = "The assistant is not available right now. Showing regular search results.";

export function AssistantEntry(props: AssistantEntryProps) {
  const { userId, flags, openStream, search } = props;
  const mode = modeFor(userId, flags.get());
  const [draft, setDraft] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [results, setResults] = useState<LegacyResult[] | null>(null);
  const s = useAssistantStream(openStream);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = draft.trim();
    if (!q) return;
    setSubmitted(q);
    setResults(null);
    if (mode === "on") s.send(q);
    else void search(q).then(setResults);
  }

  return (
    <div>
      <form role="search" onSubmit={submit}>
        <label htmlFor="kx-q">Search Kestrel</label>
        <input id="kx-q" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button type="submit">Search</button>
      </form>
      {mode === "on" && submitted !== null && (
        <section aria-label="Shopping assistant">
          <p>Answer from Kestrel&apos;s AI assistant. Check price and stock on the product page.</p>
          <div role="log" aria-live="polite" aria-label="Assistant answer">{s.text}</div>
          {s.products.length > 0 && (
            <ul aria-label="Suggested products">
              {s.products.map((p) => (
                <li key={p.sku}>
                  <a href={p.url}>{p.name}</a> {formatPrice(p.price_cents)}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
      {results && <LegacyResults results={results} />}
    </div>
  );
}

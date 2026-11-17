// Storefront search box with the assistant behind a flag. Reference solution.
import { useEffect, useRef, useState } from "react";
import { LegacyResults, type LegacyResult, type SearchFn } from "./LegacySearch";
import { useAssistantStream, type OpenStream } from "./vendor/useAssistantStream";
import { SseParser } from "./vendor/sse";
import { toAssistantEvent, formatPrice } from "./vendor/events";
import { bucketOf, hashQuery, modeFor, type AnalyticsEvent, type FlagClient, type Mode } from "./rollout";

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

interface ShadowResult {
  outcome: "done" | "error" | "timeout";
  ttftMs: number | null;
  answerChars: number;
}

/** Consume a whole assistant answer in the background; returns null when killed from outside. */
export async function runShadow(
  open: OpenStream,
  prompt: string,
  outer: AbortSignal,
  budgetMs: number,
): Promise<ShadowResult | null> {
  const ctrl = new AbortController();
  const onOuter = () => ctrl.abort();
  outer.addEventListener("abort", onOuter, { once: true });
  const t0 = Date.now();
  let ttft: number | null = null;
  let chars = 0;
  let timedOut = false;
  const timer = setTimeout(() => {
    if (ttft === null) {
      timedOut = true;
      ctrl.abort();
    }
  }, budgetMs);
  try {
    const parser = new SseParser();
    for await (const chunk of open({ prompt }, ctrl.signal)) {
      if (ctrl.signal.aborted) break;
      for (const raw of parser.push(chunk)) {
        const ev = toAssistantEvent(raw);
        if (!ev) continue;
        if (ev.type === "token") {
          if (ttft === null) ttft = Date.now() - t0;
          chars += ev.text.length;
        } else if (ev.type === "error") {
          return { outcome: "error", ttftMs: ttft, answerChars: chars };
        } else if (ev.type === "done") {
          return { outcome: "done", ttftMs: ttft, answerChars: chars };
        }
      }
    }
    if (outer.aborted) return null;
    if (timedOut) return { outcome: "timeout", ttftMs: ttft, answerChars: chars };
    return { outcome: "error", ttftMs: ttft, answerChars: chars };
  } catch {
    if (outer.aborted) return null;
    return { outcome: timedOut ? "timeout" : "error", ttftMs: ttft, answerChars: chars };
  } finally {
    clearTimeout(timer);
    outer.removeEventListener("abort", onOuter);
  }
}

export function AssistantEntry(props: AssistantEntryProps) {
  const { userId, flags, openStream, search, track, onHandoff } = props;
  const budget = props.ttftBudgetMs ?? 4000;

  const [flagValues, setFlagValues] = useState(() => flags.get());
  useEffect(() => {
    setFlagValues(flags.get());
    return flags.subscribe((v) => setFlagValues(v));
  }, [flags]);
  const mode: Mode = modeFor(userId, flagValues);
  const bucket = bucketOf(userId);

  const [draft, setDraft] = useState("");
  const [submitted, setSubmitted] = useState<string | null>(null);
  const [results, setResults] = useState<LegacyResult[] | null>(null);
  const [fallback, setFallback] = useState<null | "error" | "slow">(null);
  const s = useAssistantStream(openStream);

  const shadowCtrl = useRef<AbortController | null>(null);
  const searchRun = useRef(0);
  const live = useRef({ mode, bucket, submitted, track, search, s });
  live.current = { mode, bucket, submitted, track, search, s };

  const base = (q: string, m: Mode) => ({ mode: m, bucket: live.current.bucket, queryHash: hashQuery(q), queryLength: q.length });

  function runLegacy(q: string) {
    const run = ++searchRun.current;
    void live.current.search(q).then(
      (r) => { if (run === searchRun.current) setResults(r); },
      () => { if (run === searchRun.current) setResults([]); },
    );
  }

  function fallBack(reason: "error" | "slow") {
    const { submitted: q, s: stream } = live.current;
    if (!q) return;
    if (reason === "slow") stream.stop();
    setFallback(reason);
    live.current.track({ name: "assistant_fallback", ...base(q, "on"), reason });
    runLegacy(q);
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = draft.trim();
    if (!q) return;
    setSubmitted(q);
    setResults(null);
    setFallback(null);
    shadowCtrl.current?.abort();
    if (mode !== "off") track({ name: "assistant_query", ...base(q, mode) });
    if (mode === "off") {
      runLegacy(q);
    } else if (mode === "shadow") {
      runLegacy(q);
      const c = new AbortController();
      shadowCtrl.current = c;
      void runShadow(openStream, q, c.signal, budget).then((r) => {
        if (r && !c.signal.aborted) live.current.track({ name: "assistant_shadow_result", ...base(q, "shadow"), ...r });
      });
    } else {
      s.send(q);
    }
  }

  // Kill switch or a cohort change: stop whatever no longer applies, without a reload.
  useEffect(() => {
    if (mode !== "on") live.current.s.stop();
    if (mode !== "shadow") shadowCtrl.current?.abort();
    const q = live.current.submitted;
    if (mode === "off" && q) runLegacy(q);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  // Assistant failed: fall back to legacy results.
  useEffect(() => {
    if (mode === "on" && s.status === "error" && !fallback) fallBack("error");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [s.status, mode]);

  // No first token within the budget: fall back.
  const waitingFirstToken = mode === "on" && s.status === "streaming" && s.text === "";
  useEffect(() => {
    if (!waitingFirstToken) return;
    const t = setTimeout(() => fallBack("slow"), budget);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [waitingFirstToken, budget]);

  useEffect(() => () => shadowCtrl.current?.abort(), []);

  const showAssistant = mode === "on" && submitted !== null && fallback === null;

  return (
    <div>
      <form role="search" onSubmit={submit}>
        <label htmlFor="kx-q">Search Kestrel</label>
        <input id="kx-q" value={draft} onChange={(e) => setDraft(e.target.value)} />
        <button type="submit">Search</button>
      </form>
      {showAssistant && (
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
          <button type="button" onClick={() => submitted && runLegacy(submitted)}>Show regular results</button>
          {onHandoff && (
            <button
              type="button"
              onClick={() => {
                track({ name: "assistant_handoff", ...base(submitted ?? "", "on"), conversationId: s.conversationId ?? null });
                onHandoff(s.conversationId ?? null);
              }}
            >
              Talk to a person
            </button>
          )}
        </section>
      )}
      {fallback && <p role="status">{FALLBACK_NOTICE}</p>}
      {results && <LegacyResults results={results} />}
    </div>
  );
}

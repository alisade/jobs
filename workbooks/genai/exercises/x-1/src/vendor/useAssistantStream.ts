// React hook that drives one streamed assistant answer at a time.
import { useCallback, useEffect, useRef, useState } from "react";
import { SseParser } from "./sse";
import { toAssistantEvent, type Product } from "./events";
import { StreamHttpError } from "./openStream";

export type Status = "idle" | "streaming" | "done" | "stopped" | "error";

export interface StreamRequest {
  prompt: string;
  conversationId?: string;
}

export type OpenStream = (req: StreamRequest, signal: AbortSignal) => AsyncIterable<string>;

export interface StreamError {
  message: string;
  retryable: boolean;
}

export interface AssistantStream {
  status: Status;
  text: string;
  products: Product[];
  error: StreamError | null;
  conversationId?: string;
  send: (prompt: string) => void;
  stop: () => void;
  retry: () => void;
}

export const MESSAGES = {
  connectionLost: "Connection lost. Your answer was cut off.",
  busy: "The assistant is busy right now.",
  unavailable: "The assistant is unavailable.",
};

function isAbort(e: unknown): boolean {
  return !!e && typeof e === "object" && (e as { name?: string }).name === "AbortError";
}

export function errorFor(e: unknown): StreamError {
  if (e instanceof StreamHttpError) {
    if (e.status === 429 || e.status === 503) return { message: MESSAGES.busy, retryable: true };
    return { message: MESSAGES.unavailable, retryable: e.status >= 500 };
  }
  return { message: MESSAGES.connectionLost, retryable: true };
}

export function useAssistantStream(open: OpenStream): AssistantStream {
  const [status, setStatus] = useState<Status>("idle");
  const [text, setText] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<StreamError | null>(null);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  const ctrl = useRef<AbortController | null>(null);
  const run = useRef(0);
  const lastPrompt = useRef("");
  const convRef = useRef<string | undefined>(undefined);
  const openRef = useRef(open);
  openRef.current = open;

  const send = useCallback((prompt: string) => {
    const p = prompt.trim();
    if (!p) return;
    ctrl.current?.abort();
    const c = new AbortController();
    ctrl.current = c;
    const myRun = ++run.current;
    lastPrompt.current = p;
    setText("");
    setProducts([]);
    setError(null);
    setStatus("streaming");

    const live = () => run.current === myRun && !c.signal.aborted;

    (async () => {
      const parser = new SseParser();
      let finished = false;
      try {
        const stream = openRef.current({ prompt: p, conversationId: convRef.current }, c.signal);
        outer: for await (const chunk of stream) {
          if (!live()) break;
          for (const raw of parser.push(chunk)) {
            const ev = toAssistantEvent(raw);
            if (!ev) continue;
            if (ev.type === "meta") {
              convRef.current = ev.conversationId;
              setConversationId(ev.conversationId);
            } else if (ev.type === "token") {
              setText((t) => t + ev.text);
            } else if (ev.type === "product") {
              setProducts((ps) => (ps.some((x) => x.sku === ev.product.sku) ? ps : [...ps, ev.product]));
            } else if (ev.type === "error") {
              finished = true;
              setError({ message: ev.message, retryable: ev.retryable });
              setStatus("error");
              break outer;
            } else if (ev.type === "done") {
              finished = true;
              setStatus("done");
              break outer;
            }
          }
        }
        parser.flush();
        if (!finished && live()) {
          setError({ message: MESSAGES.connectionLost, retryable: true });
          setStatus("error");
        }
      } catch (e) {
        if (isAbort(e) || !live()) return;
        setError(errorFor(e));
        setStatus("error");
      }
    })();
  }, []);

  const stop = useCallback(() => {
    if (!ctrl.current || ctrl.current.signal.aborted) return;
    ctrl.current.abort();
    run.current++;
    setStatus((s) => (s === "streaming" ? "stopped" : s));
  }, []);

  const retry = useCallback(() => {
    if (lastPrompt.current) send(lastPrompt.current);
  }, [send]);

  useEffect(() => () => {
    run.current++;
    ctrl.current?.abort();
  }, []);

  return { status, text, products, error, conversationId, send, stop, retry };
}

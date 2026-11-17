// React hook that drives one streamed assistant answer at a time.
import { useCallback, useRef, useState } from "react";
import { SseParser } from "./sse";
import { toAssistantEvent, type Product } from "./events";

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

// Use these exact strings (the support team's macros quote them).
export const MESSAGES = {
  connectionLost: "Connection lost. Your answer was cut off.",
  busy: "The assistant is busy right now.",
  unavailable: "The assistant is unavailable.",
};

// TODO: stop(), retry(), error events and thrown errors, stream ending without "done",
// conversation id from the meta event (sent with the next request), ignoring a stale run after
// stop or a new send, aborting on unmount, no duplicate product cards. See README.
export function useAssistantStream(open: OpenStream): AssistantStream {
  const [status, setStatus] = useState<Status>("idle");
  const [text, setText] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const ctrl = useRef<AbortController | null>(null);

  const send = useCallback((prompt: string) => {
    const c = new AbortController();
    ctrl.current = c;
    setText("");
    setProducts([]);
    setStatus("streaming");
    (async () => {
      const parser = new SseParser();
      for await (const chunk of open({ prompt }, c.signal)) {
        for (const raw of parser.push(chunk)) {
          const ev = toAssistantEvent(raw);
          if (!ev) continue;
          if (ev.type === "token") setText((t) => t + ev.text);
          if (ev.type === "product") setProducts((ps) => [...ps, ev.product]);
          if (ev.type === "done") setStatus("done");
        }
      }
    })();
  }, [open]);

  const stop = useCallback(() => {
    // TODO
  }, []);

  const retry = useCallback(() => {
    // TODO
  }, []);

  return { status, text, products, error: null, send, stop, retry };
}

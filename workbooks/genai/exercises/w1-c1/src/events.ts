// Typed events of the Kestrel assistant gateway stream (see README "Stream contract").
// This file is complete: use it from the hook. Unknown or malformed events map to null.
import type { SseEvent } from "./sse";

export interface Product {
  sku: string;
  name: string;
  price_cents: number;
  in_stock: boolean;
  url: string;
}

export type AssistantEvent =
  | { type: "meta"; conversationId: string; model: string }
  | { type: "token"; text: string }
  | { type: "product"; product: Product }
  | { type: "error"; code: string; message: string; retryable: boolean }
  | { type: "done"; stopReason: string };

function json(data: string): unknown {
  try {
    return JSON.parse(data);
  } catch {
    return undefined;
  }
}

function isProduct(p: unknown): p is Product {
  if (!p || typeof p !== "object") return false;
  const o = p as Record<string, unknown>;
  return (
    typeof o.sku === "string" &&
    typeof o.name === "string" &&
    typeof o.price_cents === "number" &&
    Number.isInteger(o.price_cents) &&
    typeof o.in_stock === "boolean" &&
    typeof o.url === "string"
  );
}

export function toAssistantEvent(e: SseEvent): AssistantEvent | null {
  const d = json(e.data) as Record<string, unknown> | undefined;
  if (!d || typeof d !== "object") return null;
  switch (e.event) {
    case "meta":
      return typeof d.conversation_id === "string"
        ? { type: "meta", conversationId: d.conversation_id, model: String(d.model ?? "") }
        : null;
    case "token":
      return typeof d.text === "string" ? { type: "token", text: d.text } : null;
    case "product":
      return isProduct(d) ? { type: "product", product: d } : null;
    case "error":
      return {
        type: "error",
        code: String(d.code ?? "unknown"),
        message: String(d.message ?? "The assistant had a problem."),
        retryable: d.retryable === true,
      };
    case "done":
      return { type: "done", stopReason: String(d.stop_reason ?? "end_turn") };
    default:
      return null;
  }
}

export function formatPrice(cents: number): string {
  return "$" + (cents / 100).toFixed(2);
}

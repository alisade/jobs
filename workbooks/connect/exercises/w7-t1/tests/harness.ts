// Harness for w7-t1: runs a bot handoff through this checkout's flows and module with connect-kit.
import * as fs from "fs";
import * as path from "path";
import { simulate, Flow, SimResult } from "connect-kit";

export const root = path.resolve(__dirname, __dirname.endsWith("__hidden__") ? "../.." : "..");
export const load = (p: string): Flow => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
export const res = JSON.parse(fs.readFileSync(path.join(root, "config/resources.json"), "utf8"));
export const voiceFlow = () => load("flows/helpdesk-voice-inbound.json");
export const chatFlow = () => load("flows/helpdesk-chat-inbound.json");
export const handoffModule = () => load("modules/lfg-handoff.json");

export type Turn = { intent: string; summary?: string; slots?: Record<string, string>; verified?: string } | { error: string };

export function handoff(channel: "VOICE" | "CHAT", turn: Turn): SimResult & { queueName: string } {
  const lex = "error" in turn
    ? [{ error: turn.error }]
    : [{
        intent: turn.intent,
        slots: turn.slots || {},
        sessionAttributes: {
          botSummary: turn.summary ?? "Locked out after replacing phone",
          lexSlots: JSON.stringify(turn.slots || { device: "new phone" }),
          callerVerified: turn.verified ?? "true",
        },
      }];
  const r = simulate(channel === "VOICE" ? voiceFlow() : chatFlow(), {
    channel,
    lex: lex as any,
    modules: { [res.modules["lfg-handoff"]]: handoffModule() },
  });
  const q = r.queue || "";
  return { ...r, queueName: q.endsWith("q-password-reset") ? "PasswordReset" : q.endsWith("q-general-support") ? "GeneralSupport" : q };
}

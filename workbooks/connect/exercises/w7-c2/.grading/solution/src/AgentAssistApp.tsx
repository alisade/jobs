// LFG help desk workspace app: shows the bot handoff context, a guided-resolution checklist and
// ranked knowledge suggestions, and resolves the ServiceNow incident through the backend.
import React, { useCallback, useEffect, useRef, useState } from "react";
import { ContactEventSource, ContactLifecycleEvent, HANDOFF_KEYS } from "./workspace";
import { IncidentApi } from "./api";
import { Guide, GuideBook, canResolve, guideFor, initialChecks } from "./guide";
import { Suggestion } from "./rank";

export type Props = {
  client: ContactEventSource;
  api: IncidentApi;
  guides: GuideBook;
  loadSuggestions: (ctx: HandoffContext) => Promise<Suggestion[]>;
};

export type HandoffContext = {
  contactId: string;
  channel: string;
  summary: string;
  intent: string;
  slots: Record<string, string>;
  slotsError: boolean;
  incidentNumber: string;
  incidentSysId: string;
  verified: boolean;
  vip: boolean;
};

export function parseContext(contactId: string, type: string, a: Record<string, string>): HandoffContext {
  let slots: Record<string, string> = {};
  let slotsError = false;
  if (a.lexSlots) {
    try {
      const parsed = JSON.parse(a.lexSlots);
      if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
        for (const [k, v] of Object.entries(parsed)) if (v !== null && v !== undefined && v !== "") slots[k] = String(v);
      } else slotsError = true;
    } catch {
      slotsError = true;
    }
  }
  return {
    contactId,
    channel: a.channel || type,
    summary: a.botSummary || "",
    intent: a.lexIntent || "",
    slots,
    slotsError,
    incidentNumber: a.incidentNumber || "",
    incidentSysId: a.incidentSysId || "",
    verified: a.callerVerified === "true",
    vip: a.vip === "true",
  };
}

export function AgentAssistApp({ client, api, guides, loadSuggestions }: Props) {
  const [ctx, setCtx] = useState<HandoffContext | null>(null);
  const [guide, setGuide] = useState<Guide | null>(null);
  const [checks, setChecks] = useState<Record<string, boolean>>({});
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [status, setStatus] = useState<{ kind: "idle" | "saving" | "ok" | "error"; text: string }>({ kind: "idle", text: "" });
  const current = useRef<string | null>(null);

  const onConnected = useCallback(
    async (e: ContactLifecycleEvent) => {
      current.current = e.contactId;
      const attrs = await client.getAttributes(e.contactId, [...HANDOFF_KEYS]);
      if (current.current !== e.contactId) return; // a newer contact connected meanwhile
      const c = parseContext(e.contactId, e.type, attrs);
      const g = guideFor(guides, c.intent);
      setCtx(c);
      setGuide(g);
      setChecks(initialChecks(g, c.verified));
      setStatus({ kind: "idle", text: "" });
      setSuggestions([]);
      try {
        const s = await loadSuggestions(c);
        if (current.current === e.contactId) setSuggestions(s);
      } catch {
        if (current.current === e.contactId) setSuggestions([]);
      }
    },
    [client, guides, loadSuggestions],
  );

  const onCleared = useCallback((e: ContactLifecycleEvent) => {
    if (current.current !== e.contactId) return;
    current.current = null;
    setCtx(null);
    setGuide(null);
    setChecks({});
    setSuggestions([]);
    setStatus({ kind: "idle", text: "" });
  }, []);

  useEffect(() => {
    client.onConnected(onConnected);
    client.onCleared(onCleared);
    return () => {
      client.offConnected(onConnected);
      client.offCleared(onCleared);
    };
  }, [client, onConnected, onCleared]);

  if (!ctx || !guide) return <div role="status">Waiting for a contact</div>;

  const resolve = async () => {
    setStatus({ kind: "saving", text: "Saving" });
    const done = guide.steps.filter((s) => checks[s.id]).map((s) => `[x] ${s.text}`);
    try {
      const r = await api.updateIncident(ctx.incidentSysId, {
        work_notes: `Resolved by agent via guided workflow "${guide.title}" (contact ${ctx.contactId}).\n${done.join("\n")}`,
        state: "6",
        close_code: "Solved (Permanently)",
        close_notes: ctx.summary,
      });
      setStatus({ kind: "ok", text: `${r.number} resolved` });
    } catch (err) {
      setStatus({ kind: "error", text: `Could not update the incident: ${(err as Error).message}` });
    }
  };

  return (
    <div>
      <section aria-label="Handoff context">
        <h2>
          Handoff from bot ({ctx.channel}){ctx.vip ? <span aria-label="VIP"> VIP</span> : null}
        </h2>
        {!ctx.verified ? <p role="alert">Caller not verified: complete identity verification first.</p> : null}
        <p data-testid="summary">{ctx.summary || "No bot summary"}</p>
        <p data-testid="intent">Intent: {ctx.intent || "unknown"}</p>
        <ul aria-label="Slots">
          {Object.entries(ctx.slots).map(([k, v]) => (
            <li key={k}>
              {k}: {v}
            </li>
          ))}
        </ul>
        {ctx.slotsError ? <p data-testid="slots-error">Slot data unavailable</p> : null}
        <p data-testid="incident">{ctx.incidentNumber ? `Incident ${ctx.incidentNumber}` : "No incident yet"}</p>
      </section>
      <section aria-label="Guided resolution">
        <h3>{guide.title}</h3>
        {guide.steps.map((s) => (
          <label key={s.id}>
            <input
              type="checkbox"
              checked={!!checks[s.id]}
              onChange={(ev) => setChecks({ ...checks, [s.id]: ev.target.checked })}
            />
            {s.text}
            {s.required ? " (required)" : ""}
          </label>
        ))}
        <button type="button" onClick={resolve} disabled={!canResolve(guide, checks) || !ctx.incidentSysId || status.kind === "saving" || status.kind === "ok"}>
          Resolve incident
        </button>
        {status.kind === "ok" ? <p role="status">{status.text}</p> : null}
        {status.kind === "error" ? <p role="alert">{status.text}</p> : null}
      </section>
      <section aria-label="Knowledge suggestions">
        <ol>
          {suggestions.map((s) => (
            <li key={s.articleId} data-testid="suggestion">
              {s.title}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

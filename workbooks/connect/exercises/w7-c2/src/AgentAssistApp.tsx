// LFG help desk workspace app: shows the bot handoff context, a guided-resolution checklist and
// ranked knowledge suggestions, and resolves the ServiceNow incident through the backend.
// Prototype from the hackathon: see README for what is missing.
import React, { useEffect, useState } from "react";
import { ContactEventSource, ContactLifecycleEvent } from "./workspace";
import { IncidentApi } from "./api";
import { GuideBook, guideFor } from "./guide";
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
  return {
    contactId,
    channel: a.channel || type,
    summary: a.botSummary || "",
    intent: a.lexIntent || "",
    slots: JSON.parse(a.lexSlots || "{}"),
    slotsError: false,
    incidentNumber: a.incidentNumber || "",
    incidentSysId: a.incidentSysId || "",
    verified: a.callerVerified === "true",
    vip: a.vip === "true",
  };
}

export function AgentAssistApp({ client, api, guides, loadSuggestions }: Props) {
  const [ctx, setCtx] = useState<HandoffContext | null>(null);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  useEffect(() => {
    client.onConnected(async (e: ContactLifecycleEvent) => {
      const attrs = await client.getAttributes(e.contactId, "*");
      const c = parseContext(e.contactId, e.type, attrs);
      setCtx(c);
      setSuggestions(await loadSuggestions(c));
    });
    // TODO: cleared contacts, unsubscribe on unmount
  }, [client, loadSuggestions]);

  if (!ctx) return <div role="status">Waiting for a contact</div>;
  const guide = guideFor(guides, ctx.intent);

  return (
    <div>
      <section aria-label="Handoff context">
        <h2>Handoff from bot ({ctx.channel})</h2>
        <p data-testid="summary">{ctx.summary}</p>
        <p data-testid="intent">Intent: {ctx.intent}</p>
        <p data-testid="incident">Incident {ctx.incidentNumber}</p>
      </section>
      <section aria-label="Guided resolution">
        <h3>{guide?.title}</h3>
        {/* TODO: checklist with checkboxes, required steps, verified pre-check */}
        <button type="button" onClick={() => api.updateIncident(ctx.incidentSysId, { work_notes: "resolved", state: "6" })}>
          Resolve incident
        </button>
      </section>
      <section aria-label="Knowledge suggestions">
        <ol>
          {suggestions.map((s) => (
            <li key={s.articleId + s.source} data-testid="suggestion">
              {s.title}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

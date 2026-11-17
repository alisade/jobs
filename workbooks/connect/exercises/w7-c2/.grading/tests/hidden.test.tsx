// Hidden tests for connect/w7-c2 (run from tests/__hidden__).
import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { FakeContactClient, appMod, rankMod, apiMod, guideMod, guides, resetHandoff, fakeApi, fixture } from "../fakeWorkspace";

const recs = fixture("fixtures/agent-assist-recommendations.json").recommendations;
const kb = fixture("fixtures/kb-retrieve.json").retrievalResults;
const catalog = fixture("fixtures/article-catalog.json");
const noSuggestions = async () => [];

describe("rankSuggestions", () => {
  const rank = (departments: string[], extra: any = {}) => rankMod.rankSuggestions(recs, kb, { catalog, departments, ...extra });
  test("dedupes the same article from both sources, keeping the higher score", () => {
    const r = rank([]);
    expect(r.filter((s) => s.articleId === "c-pwd-001")).toHaveLength(1);
    expect(r.find((s) => s.articleId === "c-pwd-001")!.score).toBeCloseTo(0.91);
  });
  test("drops articles from departments the agent is not entitled to", () => {
    const ids = rank([]).map((s) => s.articleId);
    expect(ids).not.toContain("c-exec-pwd-002");
    expect(ids).not.toContain("c-trade-pwd-007");
  });
  test("entitled departments are included", () => {
    expect(rank(["executive-office"]).map((s) => s.articleId)).toContain("c-exec-pwd-002");
  });
  test("drops low-relevance results (default floor 0.4)", () => {
    expect(rank(["executive-office", "trading"]).map((s) => s.articleId)).not.toContain("c-print-220");
  });
  test("orders by score descending and caps the list", () => {
    const r = rank(["executive-office", "trading"], { max: 3 });
    expect(r).toHaveLength(3);
    expect(r.map((s) => s.articleId)).toEqual(["c-pwd-001", "c-lock-014", "c-mfa-031"]);
  });
  test("an article with no catalog entry or department is treated as not entitled", () => {
    const r = rankMod.rankSuggestions([{ recommendationId: "x", relevanceScore: 0.99, type: "KNOWLEDGE_CONTENT", document: { contentReference: { contentId: "c-unknown" }, title: { text: "Unknown" } } }], [], { catalog, departments: [] });
    expect(r).toEqual([]);
  });
});

describe("guides", () => {
  test("unknown intent falls back to the default triage guide", () => {
    expect(guideMod.guideFor(guides, "OrderPizza").title).toBe("General triage");
    expect(guideMod.guideFor(guides, undefined).title).toBe("General triage");
  });
  test("verified callers get the identity step pre-checked", () => {
    const g = guideMod.guideFor(guides, "ResetPassword");
    expect(guideMod.initialChecks(g, true).verify).toBe(true);
    expect(guideMod.initialChecks(g, false).verify).toBe(false);
  });
  test("resolve needs every required step, not the optional ones", () => {
    const g = guideMod.guideFor(guides, "ResetPassword");
    expect(guideMod.canResolve(g, { verify: true, lockout: true, reset: true, confirm: false })).toBe(false);
    expect(guideMod.canResolve(g, { verify: true, lockout: true, reset: true, confirm: true })).toBe(true);
  });
});

describe("backend client", () => {
  test("PATCHes the incident with a bearer token", async () => {
    const calls: any[] = [];
    const f = (async (url: string, init: any) => { calls.push({ url, init }); return { ok: true, status: 200, json: async () => ({ number: "INC1", state: "6" }) }; }) as any;
    const api = apiMod.createIncidentApi("https://api.lfg.example", async () => "tok-1", f);
    await api.updateIncident("0a1b2c3d4e5f60718293a4b5c6d7e8f9", { work_notes: "x", state: "6" });
    expect(calls[0].url).toBe("https://api.lfg.example/incidents/0a1b2c3d4e5f60718293a4b5c6d7e8f9");
    expect(calls[0].init.method).toBe("PATCH");
    expect(calls[0].init.headers.Authorization).toBe("Bearer tok-1");
  });
  test("non-2xx throws; a malformed sys_id is rejected before any request", async () => {
    const f = (async () => ({ ok: false, status: 503, json: async () => ({}) })) as any;
    const api = apiMod.createIncidentApi("https://api.lfg.example", async () => "t", f);
    await expect(api.updateIncident("0a1b2c3d4e5f60718293a4b5c6d7e8f9", { work_notes: "x" })).rejects.toThrow();
    let called = false;
    const g = (async () => { called = true; return { ok: true, json: async () => ({}) }; }) as any;
    await expect(apiMod.createIncidentApi("https://api", async () => "t", g).updateIncident("../admin", { work_notes: "x" })).rejects.toThrow();
    expect(called).toBe(false);
  });
});

describe("app", () => {
  test("asks the workspace only for the handoff keys (never '*')", async () => {
    const client = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff());
    expect(client.getAttributesCalls[0].keys).not.toBe("*");
    expect(document.body.textContent).not.toContain("123-45-6789");
  });
  test("malformed lexSlots does not crash the app", async () => {
    const client = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff({ lexSlots: "{not json" }));
    expect(screen.getByTestId("summary")).toHaveTextContent(/locked out/);
    expect(screen.getByTestId("slots-error")).toBeInTheDocument();
  });
  test("unverified caller: warning shown and resolve stays disabled until verification is ticked", async () => {
    const client = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff({ callerVerified: "false" }));
    expect(screen.getByRole("alert")).toHaveTextContent(/not verified/i);
    const boxes = screen.getAllByRole("checkbox");
    for (const b of boxes.slice(1, 4)) fireEvent.click(b);
    expect(screen.getByRole("button", { name: /resolve/i })).toBeDisabled();
    fireEvent.click(boxes[0]);
    expect(screen.getByRole("button", { name: /resolve/i })).toBeEnabled();
  });
  test("resolve sends work notes listing the completed steps and shows success", async () => {
    const client = new FakeContactClient();
    const api = fakeApi();
    render(<appMod.AgentAssistApp client={client} api={api} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff());
    const boxes = screen.getAllByRole("checkbox");
    for (const b of boxes.slice(1, 4)) fireEvent.click(b);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: /resolve/i })); });
    expect(api.calls).toHaveLength(1);
    expect(api.calls[0].sysId).toBe("0a1b2c3d4e5f60718293a4b5c6d7e8f9");
    expect(api.calls[0].update.state).toBe("6");
    expect(api.calls[0].update.work_notes).toMatch(/Send the self-service reset link/);
    expect(screen.getByRole("status")).toHaveTextContent(/resolved/i);
  });
  test("backend failure is shown to the agent and resolve can be retried", async () => {
    const client = new FakeContactClient();
    const api = fakeApi(true);
    render(<appMod.AgentAssistApp client={client} api={api} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff());
    for (const b of screen.getAllByRole("checkbox").slice(1, 4)) fireEvent.click(b);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: /resolve/i })); });
    expect(screen.getByRole("alert")).toHaveTextContent(/could not update/i);
    expect(screen.getByRole("button", { name: /resolve/i })).toBeEnabled();
  });
  test("cleared contact resets the panel; a cleared event for another contact does not", async () => {
    const client = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff());
    await client.clear("c-other");
    expect(screen.getByTestId("summary")).toBeInTheDocument();
    await client.clear("c-1");
    expect(screen.getByRole("status")).toHaveTextContent(/waiting/i);
  });
  test("a second contact (chat concurrency) replaces the context and checklist", async () => {
    const client = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff());
    fireEvent.click(screen.getAllByRole("checkbox")[1]);
    await client.connect("c-2", resetHandoff({ lexIntent: "VpnIssue", botSummary: "VPN drops every 10 minutes" }));
    expect(screen.getByText("VPN connection problem")).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")[1]).not.toBeChecked();
  });
  test("unsubscribes from workspace events on unmount", async () => {
    const client = new FakeContactClient();
    const r = render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    r.unmount();
    expect(client.connected.size).toBe(0);
    expect(client.cleared.size).toBe(0);
  });
  test("ranked suggestions render in order; a suggestion failure leaves the rest of the panel working", async () => {
    const client = new FakeContactClient();
    const load = async () => rankMod.rankSuggestions(recs, kb, { catalog, departments: [] });
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={load} />);
    await client.connect("c-1", resetHandoff());
    expect(screen.getAllByTestId("suggestion").map((e) => e.textContent)[0]).toMatch(/Reset an Entra ID password/);
    const client2 = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client2} api={fakeApi()} guides={guides} loadSuggestions={async () => { throw new Error("assist down"); }} />);
    await client2.connect("c-9", resetHandoff());
    expect(screen.getAllByTestId("intent").length).toBe(2);
  });
  test("VIP callers are flagged", async () => {
    const client = new FakeContactClient();
    render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
    await client.connect("c-1", resetHandoff({ vip: "true" }));
    expect(screen.getByLabelText("VIP")).toBeInTheDocument();
  });
});

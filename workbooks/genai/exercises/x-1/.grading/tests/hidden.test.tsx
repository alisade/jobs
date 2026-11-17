import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssistantEntry, FALLBACK_NOTICE } from "../../src/AssistantEntry";
import { bucketOf, hashQuery, modeFor, type AnalyticsEvent } from "../../src/rollout";
import { fakeFlags, fakeSearch, sink, controlled, userFor, META, tok, DONE } from "../helpers";

const ALLOWED = new Set(["name", "mode", "bucket", "queryHash", "queryLength", "outcome", "ttftMs", "answerChars", "reason", "conversationId"]);
const Q = "gift for my coworker Emily under $50";
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function query(text: string) {
  await userEvent.type(screen.getByLabelText("Search Kestrel"), text);
  await userEvent.click(screen.getByRole("button", { name: "Search" }));
}
const answer = () => screen.queryByRole("log", { name: "Assistant answer" });

describe("cohorts", () => {
  test("bucket is stable per user and in 0-99", () => {
    for (const id of ["cust-1", "cust-88213", "guest-ab12", ""]) {
      const b = bucketOf(id);
      expect(Number.isInteger(b)).toBe(true);
      expect(b).toBeGreaterThanOrEqual(0);
      expect(b).toBeLessThan(100);
      expect(bucketOf(id)).toBe(b);
    }
  });

  test("percent rollout is roughly right and monotonic", () => {
    const flags = (percent: number) => ({ killSwitch: false, mode: "on" as const, percent });
    let in20 = 0;
    for (let i = 0; i < 5000; i++) {
      const id = `cust-${i}`;
      const a = modeFor(id, flags(20)) === "on";
      if (a) in20++;
      if (a) expect(modeFor(id, flags(60))).toBe("on");
    }
    expect(in20 / 5000).toBeGreaterThan(0.16);
    expect(in20 / 5000).toBeLessThan(0.24);
  });

  test("kill switch wins; 0 and 100 percent; out-of-range percent clamps", () => {
    expect(modeFor("cust-1", { killSwitch: true, mode: "on", percent: 100 })).toBe("off");
    expect(modeFor("cust-1", { killSwitch: false, mode: "shadow", percent: 0 })).toBe("off");
    expect(modeFor("cust-1", { killSwitch: false, mode: "shadow", percent: 100 })).toBe("shadow");
    expect(modeFor("cust-1", { killSwitch: false, mode: "on", percent: 250 })).toBe("on");
    expect(modeFor("cust-1", { killSwitch: false, mode: "on", percent: -5 })).toBe("off");
  });

  test("a user outside the percentage gets legacy search", async () => {
    const outside = userFor(modeFor, false, 50);
    const c = controlled();
    render(<AssistantEntry userId={outside} flags={fakeFlags({ killSwitch: false, mode: "on", percent: 50 }).client} openStream={c.open} search={fakeSearch()} track={sink().track} />);
    await query("tent");
    expect(await screen.findByRole("list", { name: "Search results" })).toBeInTheDocument();
    expect(c.open).not.toHaveBeenCalled();
  });
});

describe("shadow mode", () => {
  test("legacy results render; the assistant runs in the background and is only logged", async () => {
    const c = controlled();
    const an = sink();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "shadow", percent: 100 }).client} openStream={c.open} search={fakeSearch()} track={an.track} />);
    await query("tent for two");
    expect(await screen.findByRole("list", { name: "Search results" })).toHaveTextContent("Ridgeline 2P Tent");
    await waitFor(() => expect(c.open).toHaveBeenCalledTimes(1));
    expect(c.requests[0].prompt).toBe("tent for two");
    await act(async () => { c.push(META + tok(1, "The Ridgeline ") + tok(2, "fits two.") + DONE); });
    await waitFor(() => expect(an.events.some((e) => e.name === "assistant_shadow_result")).toBe(true));
    const r = an.events.find((e) => e.name === "assistant_shadow_result") as AnalyticsEvent;
    expect(r).toMatchObject({ mode: "shadow", outcome: "done", answerChars: "The Ridgeline fits two.".length });
    expect(typeof r.ttftMs).toBe("number");
    expect(answer()).toBeNull();
    expect(screen.queryByText(/fits two/)).toBeNull();
  });
});

describe("kill switch", () => {
  test("flipping it while an answer streams goes to legacy at once and aborts the stream", async () => {
    const flags = fakeFlags({ killSwitch: false, mode: "on", percent: 100 });
    const c = controlled();
    const search = fakeSearch();
    render(<AssistantEntry userId="cust-1" flags={flags.client} openStream={c.open} search={search} track={sink().track} />);
    await query("tent for two");
    await act(async () => { c.push(META + tok(1, "The Ridgeline ")); });
    await waitFor(() => expect(answer()).toHaveTextContent("The Ridgeline"));
    await act(async () => { flags.set({ killSwitch: true }); });
    expect(answer()).toBeNull();
    expect(c.signals[0].aborted).toBe(true);
    expect(await screen.findByRole("list", { name: "Search results" })).toBeInTheDocument();
    expect(search).toHaveBeenCalledWith("tent for two");
  });

  test("it also stops a shadow call, and turning it off again restores the mode live", async () => {
    const flags = fakeFlags({ killSwitch: false, mode: "shadow", percent: 100 });
    const c = controlled();
    render(<AssistantEntry userId="cust-1" flags={flags.client} openStream={c.open} search={fakeSearch()} track={sink().track} />);
    await query("tent");
    await waitFor(() => expect(c.open).toHaveBeenCalledTimes(1));
    await act(async () => { flags.set({ killSwitch: true }); });
    expect(c.signals[0].aborted).toBe(true);
    await act(async () => { flags.set({ killSwitch: false, mode: "on" }); });
    await userEvent.clear(screen.getByLabelText("Search Kestrel"));
    await query("lantern");
    await waitFor(() => expect(c.open).toHaveBeenCalledTimes(2));
    expect(answer()).not.toBeNull();
  });

  test("the flag subscription is released on unmount", () => {
    const flags = fakeFlags({ killSwitch: false, mode: "on", percent: 100 });
    const { unmount } = render(<AssistantEntry userId="cust-1" flags={flags.client} openStream={controlled().open} search={fakeSearch()} track={sink().track} />);
    expect(flags.subscribers()).toBe(1);
    unmount();
    expect(flags.subscribers()).toBe(0);
  });
});

describe("fallback", () => {
  test("an assistant error shows legacy results and the notice", async () => {
    const c = controlled();
    const an = sink();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "on", percent: 100 }).client} openStream={c.open} search={fakeSearch()} track={an.track} />);
    await query("tent");
    await act(async () => { c.push('event: error\ndata: {"code": "overloaded", "message": "busy", "retryable": true}\n\n'); });
    expect(await screen.findByRole("status")).toHaveTextContent(FALLBACK_NOTICE);
    expect(await screen.findByRole("list", { name: "Search results" })).toBeInTheDocument();
    expect(an.events.filter((e) => e.name === "assistant_fallback").map((e) => e.reason)).toEqual(["error"]);
  });

  test("no first token within the budget: abort, fall back, log reason slow", async () => {
    const c = controlled();
    const an = sink();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "on", percent: 100 }).client} openStream={c.open} search={fakeSearch()} track={an.track} ttftBudgetMs={60} />);
    await query("tent");
    expect(await screen.findByRole("status", {}, { timeout: 2000 })).toHaveTextContent(FALLBACK_NOTICE);
    expect(c.signals[0].aborted).toBe(true);
    expect(await screen.findByRole("list", { name: "Search results" })).toBeInTheDocument();
    expect(an.events.find((e) => e.name === "assistant_fallback")?.reason).toBe("slow");
  });

  test("a first token inside the budget means no fallback", async () => {
    const c = controlled();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "on", percent: 100 }).client} openStream={c.open} search={fakeSearch()} track={sink().track} ttftBudgetMs={400} />);
    await query("tent");
    await act(async () => { c.push(META + tok(1, "The Ridgeline ")); });
    await act(async () => { await sleep(700); });
    expect(screen.queryByRole("status")).toBeNull();
    expect(c.signals[0].aborted).toBe(false);
    expect(answer()).toHaveTextContent("The Ridgeline");
  });
});

describe("on mode extras", () => {
  test("legacy results are one click away while the answer stays", async () => {
    const c = controlled();
    const search = fakeSearch();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "on", percent: 100 }).client} openStream={c.open} search={search} track={sink().track} />);
    await query("tent");
    await act(async () => { c.push(META + tok(1, "Try the Ridgeline.") + DONE); });
    await userEvent.click(screen.getByRole("button", { name: "Show regular results" }));
    expect(await screen.findByRole("list", { name: "Search results" })).toBeInTheDocument();
    expect(answer()).toHaveTextContent("Try the Ridgeline.");
  });

  test("handoff passes the conversation id and is tracked", async () => {
    const c = controlled();
    const an = sink();
    const onHandoff = jest.fn();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "on", percent: 100 }).client} openStream={c.open} search={fakeSearch()} track={an.track} onHandoff={onHandoff} />);
    await query("where is my order");
    await act(async () => { c.push(META + tok(1, "Let me check.") + DONE); });
    await userEvent.click(await screen.findByRole("button", { name: "Talk to a person" }));
    expect(onHandoff).toHaveBeenCalledWith("c-5501");
    expect(an.events.find((e) => e.name === "assistant_handoff")?.conversationId).toBe("c-5501");
  });
});

describe("analytics schema", () => {
  test("events use only the allowed fields and never carry the query text or the user id", async () => {
    const userId = "cust-88213";
    const flags = fakeFlags({ killSwitch: false, mode: "shadow", percent: 100 });
    const c = controlled();
    const an = sink();
    render(<AssistantEntry userId={userId} flags={flags.client} openStream={c.open} search={fakeSearch()} track={an.track} onHandoff={() => undefined} />);
    await query(Q);
    await waitFor(() => expect(c.open).toHaveBeenCalledTimes(1));
    await act(async () => { c.push(META + tok(1, "Here are three ideas.") + DONE); });
    await waitFor(() => expect(an.events.some((e) => e.name === "assistant_shadow_result")).toBe(true));
    await act(async () => { flags.set({ mode: "on" }); });
    await userEvent.clear(screen.getByLabelText("Search Kestrel"));
    await query(Q);
    await act(async () => { c.push(META + tok(1, "Here are three ideas.") + DONE); });
    await userEvent.click(await screen.findByRole("button", { name: "Talk to a person" }));

    const names = an.events.map((e) => e.name);
    expect(names.filter((n) => n === "assistant_query")).toHaveLength(2);
    expect(names).toContain("assistant_handoff");
    for (const e of an.events) {
      for (const k of Object.keys(e)) expect(ALLOWED.has(k)).toBe(true);
      const json = JSON.stringify(e);
      expect(json).not.toContain("Emily");
      expect(json).not.toContain("coworker");
      expect(json).not.toContain(userId);
      expect(e.queryHash).toBe(hashQuery(Q));
      expect(e.queryLength).toBe(Q.length);
      expect(e.bucket).toBe(bucketOf(userId));
    }
    expect(hashQuery(Q)).not.toContain("Emily");
    expect(hashQuery("a")).not.toBe(hashQuery("b"));
  });

  test("off mode sends no assistant events", async () => {
    const an = sink();
    render(<AssistantEntry userId="cust-1" flags={fakeFlags({ killSwitch: false, mode: "off", percent: 100 }).client} openStream={controlled().open} search={fakeSearch()} track={an.track} />);
    await query("tent");
    await screen.findByRole("list", { name: "Search results" });
    expect(an.events).toHaveLength(0);
  });
});

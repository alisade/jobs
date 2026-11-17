import { firstValueFrom, from, toArray } from "rxjs";
import { createLeakGuard, WITHHELD } from "../../src/leakGuard";
import { parseSse } from "../../src/sse";
import { TutorChatStore } from "../../src/tutorChat";
import { TutorEvent } from "../../src/types";
import { bytes, cut, FakeApi, sse } from "../helpers";

const parse = (chunks: Uint8Array[]) => firstValueFrom(parseSse(from(chunks)).pipe(toArray()));
const tokens = (evs: TutorEvent[]) => evs.filter((e) => e.type === "token").map((e: any) => e.text).join("");

describe("parseSse", () => {
  const body = sse("token", { text: "Vaccines train " }) + sse("token", { text: "the adaptive immune system." }) +
    sse("citation", { sectionId: "l5-s1" }) + sse("done");

  test("events cut at every possible byte offset", async () => {
    const b = bytes(body);
    for (let i = 1; i < b.length; i++) {
      const evs = await parse(cut(b, [i]));
      expect(evs.length).toBe(4);
      expect(tokens(evs)).toBe("Vaccines train the adaptive immune system.");
    }
  });

  test("one byte per chunk", async () => {
    const b = bytes(body);
    const evs = await parse(cut(b, Array.from({ length: b.length - 1 }, (_, i) => i + 1)));
    expect(evs.map((e) => e.type)).toEqual(["token", "token", "citation", "done"]);
  });

  test("multi-byte characters split across chunks", async () => {
    const b = bytes(sse("token", { text: "Caf\u00e9 \u00b5m \u2248 \u4e2d" }) + sse("done"));
    const evs = await parse(cut(b, [22, 23, 26, 27, 31]));
    expect(tokens(evs)).toBe("Caf\u00e9 \u00b5m \u2248 \u4e2d");
  });

  test("CRLF line endings and keep-alive comments", async () => {
    const raw = ": keep-alive\r\n\r\nevent: token\r\ndata: {\"text\":\"ok\"}\r\n\r\nevent: done\r\n\r\n";
    const evs = await parse([bytes(raw)]);
    expect(evs).toEqual([{ type: "token", text: "ok" }, { type: "done" }]);
  });

  test("multi-line data is joined with newlines", async () => {
    const raw = "event: token\ndata: {\"text\":\ndata: \"two lines\"}\n\n";
    const evs = await parse([bytes(raw)]);
    expect(evs).toEqual([{ type: "token", text: "two lines" }]);
  });

  test("a truncated final event is dropped, not half-emitted", async () => {
    const evs = await parse([bytes(sse("token", { text: "a" }) + "event: token\ndata: {\"te")]);
    expect(evs).toEqual([{ type: "token", text: "a" }]);
  });
});

describe("leak guard", () => {
  test("catches a secret split across tokens, any case", () => {
    const g = createLeakGuard(["memory cells"]);
    const out = ["They make Mem", "ory Ce", "lls that remember."].map((t) => g.push(t)).join("") + g.flush();
    expect(out.toLowerCase()).not.toContain("memory cells");
    expect(out).toContain(WITHHELD);
    expect(g.leaked).toBe(true);
  });

  test("passes ordinary text through unchanged and loses nothing", () => {
    const g = createLeakGuard(["memory cells"]);
    const parts = ["The immune ", "system keeps ", "a memory of the ", "antigen. ", "Cells divide."];
    expect(parts.map((t) => g.push(t)).join("") + g.flush()).toBe(parts.join(""));
    expect(g.leaked).toBe(false);
  });

  test("never shows a prefix of the secret before it is resolved", () => {
    const g = createLeakGuard(["droplets"]);
    const shown = g.push("Mostly by drop");
    expect(shown.toLowerCase().endsWith("drop")).toBe(false);
  });
});

describe("TutorChatStore", () => {
  const ask = (q: string, key = ["memory cells"]) => ({ question: q, lessonId: "l5", answerKey: key });

  test("a new question cancels the stream in flight", () => {
    const api = new FakeApi();
    const store = new TutorChatStore(api);
    store.ask(ask("first"));
    store.ask(ask("second"));
    expect(api.calls[0].unsubscribed).toBe(true);
    api.calls[0].body.next(bytes(sse("token", { text: "stale answer" })));
    api.calls[1].body.next(bytes(sse("token", { text: "fresh" }) + sse("done")));
    expect(store.snapshot.question).toBe("second");
    expect(store.snapshot.text).toBe("fresh");
  });

  test("redacts the answer across tokens and flushes the tail on done", () => {
    const api = new FakeApi();
    const store = new TutorChatStore(api);
    store.ask(ask("What do vaccines leave behind?"));
    api.calls[0].body.next(bytes(sse("token", { text: "They leave memo" }) + sse("token", { text: "ry cells behind" })));
    api.calls[0].body.next(bytes(sse("token", { text: " for later." }) + sse("done")));
    expect(store.snapshot.status).toBe("done");
    expect(store.snapshot.text.toLowerCase()).not.toContain("memory cells");
    expect(store.snapshot.text.endsWith(" for later.")).toBe(true);
    expect(store.snapshot.withheld).toBe(true);
  });

  test("citations are kept in order without duplicates", () => {
    const api = new FakeApi();
    const store = new TutorChatStore(api);
    store.ask(ask("q"));
    api.calls[0].body.next(bytes(sse("citation", { sectionId: "l5-s1" }) + sse("citation", { sectionId: "l4-s2" }) +
      sse("citation", { sectionId: "l5-s1" }) + sse("done")));
    expect(store.snapshot.citations).toEqual(["l5-s1", "l4-s2"]);
  });

  test("server error event and transport error both end in error state", () => {
    const api = new FakeApi();
    const store = new TutorChatStore(api);
    store.ask(ask("q1"));
    api.calls[0].body.next(bytes(sse("error", { message: "model unavailable" })));
    expect(store.snapshot.status).toBe("error");
    expect(store.snapshot.error).toBe("model unavailable");
    store.ask(ask("q2"));
    api.calls[1].body.error(new Error("network down"));
    expect(store.snapshot.status).toBe("error");
    store.ask(ask("q3"));
    expect(store.snapshot.status).toBe("streaming");
  });

  test("no first token in time is a timeout error", async () => {
    const api = new FakeApi();
    const store = new TutorChatStore(api, { firstTokenTimeoutMs: 40 });
    store.ask(ask("q"));
    await new Promise((r) => setTimeout(r, 120));
    expect(store.snapshot.status).toBe("error");
    expect(store.snapshot.error).toBe("timeout");
    expect(api.calls[0].unsubscribed).toBe(true);
  });

  test("a slow stream that started is not timed out", async () => {
    const api = new FakeApi();
    const store = new TutorChatStore(api, { firstTokenTimeoutMs: 40 });
    store.ask(ask("q"));
    api.calls[0].body.next(bytes(sse("token", { text: "Hi" })));
    await new Promise((r) => setTimeout(r, 120));
    api.calls[0].body.next(bytes(sse("done")));
    expect(store.snapshot.status).toBe("done");
  });
});

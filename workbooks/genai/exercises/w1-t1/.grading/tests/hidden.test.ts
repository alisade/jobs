import { streamAnswer } from "../../src/streamClient";
import { apply, empty } from "../../src/transcript";
import { gateway, answer, frame, FULL, WORDS } from "../gateway";
import { SseParser } from "../../src/sse";

test("guard: no drop, one connection, exact text", async () => {
  const gw = gateway(answer());
  const r = await streamAnswer(gw.connect, "q");
  expect(r).toMatchObject({ outcome: "done", connections: 1 });
  expect(r.transcript.text).toBe(FULL);
  expect(gw.requests[0].lastEventId ?? "").toBe("");
});

test("drop after a clean close: resumes with the last id it saw", async () => {
  const gw = gateway(answer(), { dropAfter: [6] }); // meta + tokens 1..5
  const r = await streamAnswer(gw.connect, "q");
  expect(gw.requests).toHaveLength(2);
  expect(gw.requests[1].lastEventId).toBe("5");
  expect(r.transcript.text).toBe(FULL);
  expect(r.outcome).toBe("done");
});

test("drop by network error: same result", async () => {
  const gw = gateway(answer(), { dropAfter: [4], throwOnDrop: true });
  const r = await streamAnswer(gw.connect, "q");
  expect(gw.requests[1].lastEventId).toBe("3");
  expect(r.transcript.text).toBe(FULL);
});

test("two drops: each reconnect sends the newest id", async () => {
  const gw = gateway(answer(), { dropAfter: [3, 4] });
  const r = await streamAnswer(gw.connect, "q");
  expect(gw.requests.map((q) => q.lastEventId ?? "")).toEqual(["", "2", "6"]);
  expect(r.transcript.text).toBe(FULL);
});

test("a half-received event from the dead connection is not applied or garbled", async () => {
  const gw = gateway(answer(), { dropAfter: [6], partialOnDrop: true });
  const r = await streamAnswer(gw.connect, "q");
  expect(gw.requests[1].lastEventId).toBe("5");
  expect(r.transcript.text).toBe(FULL);
});

test("conversation id from meta is kept across the reconnect", async () => {
  const gw = gateway(answer(), { dropAfter: [6] });
  const r = await streamAnswer(gw.connect, "q");
  expect(gw.requests[1].conversationId).toBe("c-7f3a91");
  expect(r.transcript.conversationId).toBe("c-7f3a91");
});

test("a gateway that ignores Last-Event-ID and replays: still no duplicate words", async () => {
  const gw = gateway(answer(), { dropAfter: [8, 3], ignoreLastEventId: true });
  const r = await streamAnswer(gw.connect, "q");
  expect(r.outcome).toBe("done");
  expect(r.transcript.text).toBe(FULL);
});

test("reducer is idempotent on event id", () => {
  const p = new SseParser();
  const evs = p.push(answer().map(frame).join(""));
  let t = empty;
  for (const ev of evs) t = apply(t, ev);
  for (const ev of evs.slice(1, 5)) t = apply(t, ev); // replay tokens 1..4
  expect(t.text).toBe(FULL);
  expect(t.done).toBe(true);
});

test("reducer: tokens without an id still append (older gateway builds)", () => {
  let t = empty;
  t = apply(t, { event: "token", data: JSON.stringify({ text: "a " }) });
  t = apply(t, { event: "token", data: JSON.stringify({ text: "b" }) });
  expect(t.text).toBe("a b");
});

test("guard: reconnect budget is respected and the outcome is failed", async () => {
  const gw = gateway(answer(WORDS.concat(WORDS)), { dropAfter: [2, 2, 2, 2, 2, 2] });
  const r = await streamAnswer(gw.connect, "q", { maxReconnects: 2 });
  expect(r.outcome).toBe("failed");
  expect(gw.requests).toHaveLength(3);
});

test("guard: done ends the stream without reconnecting", async () => {
  const gw = gateway(answer(), { dropAfter: [undefined, 1] });
  const r = await streamAnswer(gw.connect, "q");
  expect(r.outcome).toBe("done");
  expect(gw.requests).toHaveLength(1);
});

test("guard: abort stops without reconnecting", async () => {
  const ctrl = new AbortController();
  const gw = gateway(answer(), { dropAfter: [3] });
  const r = await streamAnswer(gw.connect, "q", {
    signal: ctrl.signal,
    onUpdate: (t) => { if (t.text.startsWith("For two")) ctrl.abort(); },
  });
  expect(r.outcome).toBe("aborted");
  expect(gw.requests).toHaveLength(1);
});

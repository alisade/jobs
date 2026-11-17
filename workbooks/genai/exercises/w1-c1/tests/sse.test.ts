/** @jest-environment node */
import { SseParser } from "../src/sse";
import { fixture, eventChunks } from "./helpers";

test("parses the recorded stream when each chunk is a whole event", () => {
  const p = new SseParser();
  const events = eventChunks(fixture("tent-question.sse")).flatMap((c) => p.push(c));
  const types = events.map((e) => e.event);
  expect(types[0]).toBe("meta");
  expect(types.filter((t) => t === "token")).toHaveLength(29);
  expect(types.filter((t) => t === "product")).toHaveLength(2);
  expect(types[types.length - 1]).toBe("done");
});

test("token events carry their id", () => {
  const p = new SseParser();
  const [ev] = p.push('id: 7\nevent: token\ndata: {"text": "hi"}\n\n');
  expect(ev).toEqual({ event: "token", data: '{"text": "hi"}', id: "7" });
});

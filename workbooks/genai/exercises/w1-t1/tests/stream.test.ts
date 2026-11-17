import { streamAnswer } from "../src/streamClient";
import { gateway, answer, FULL } from "./gateway";

test("happy path: one connection renders the whole answer", async () => {
  const gw = gateway(answer());
  const r = await streamAnswer(gw.connect, "tent for two?");
  expect(r.outcome).toBe("done");
  expect(r.transcript.text).toBe(FULL);
  expect(r.connections).toBe(1);
});

test("a dropped connection is retried", async () => {
  const gw = gateway(answer(), { dropAfter: [6] });
  const r = await streamAnswer(gw.connect, "tent for two?");
  expect(r.outcome).toBe("done");
  expect(gw.requests).toHaveLength(2);
});

// Repro from the page: the new proxy closes the stream during a long tool call. This fails until
// the incident is fixed.
test("repro: answer is intact after the proxy cuts the stream", async () => {
  const gw = gateway(answer(), { dropAfter: [6] });
  const r = await streamAnswer(gw.connect, "tent for two?");
  expect(r.transcript.text).toBe(FULL);
});

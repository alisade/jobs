import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssistantPanel } from "../../src/AssistantPanel";
import { MESSAGES } from "../../src/useAssistantStream";
import { StreamHttpError } from "../../src/openStream";
import { fixture, controlled, replay } from "../helpers";

const FULL =
  "For two people on a weekend trip, the Ridgeline 2P is the best fit: it weighs 1.9 kg and packs small. " +
  "If you want more room, look at the Basecamp 3P.";
const tok = (id: number, text: string) => `id: ${id}\nevent: token\ndata: ${JSON.stringify({ text })}\n\n`;
const META = 'event: meta\ndata: {"conversation_id": "c-7f3a91", "model": "primary"}\n\n';

function randomChunks(s: string, seed: number): string[] {
  const out: string[] = [];
  let x = seed;
  let i = 0;
  while (i < s.length) {
    x = (x * 1103515245 + 12345) % 2147483648;
    const n = 1 + (x % 23);
    out.push(s.slice(i, i + n));
    i += n;
  }
  return out;
}

async function ask(text = "tent for two?") {
  await userEvent.type(screen.getByLabelText("Ask about products"), text);
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
}
const log = () => screen.getByRole("log", { name: "Assistant answer" });

test("arbitrary network chunking renders the exact answer and both product cards", async () => {
  render(<AssistantPanel openStream={replay(randomChunks(fixture("tent-question.sse"), 7))} />);
  expect(screen.getByText(/AI assistant/i)).toBeInTheDocument();
  await ask();
  await waitFor(() => expect(log()).toHaveTextContent(FULL));
  const ridge = await screen.findByRole("article", { name: "Ridgeline 2P Tent" });
  expect(ridge).toHaveTextContent("$249.00");
  expect(ridge).toHaveTextContent("In stock");
  const base = screen.getByRole("article", { name: "Basecamp 3P Tent" });
  expect(base).toHaveTextContent("$329.00");
  expect(base).toHaveTextContent("Out of stock");
  expect(screen.queryByRole("alert")).toBeNull();
});

test("Send is disabled while streaming and for an empty box; the box clears after sending", async () => {
  const c = controlled();
  render(<AssistantPanel openStream={c.open} />);
  expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  await ask("first question");
  expect(screen.getByLabelText("Ask about products")).toHaveValue("");
  await userEvent.type(screen.getByLabelText("Ask about products"), "second");
  expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  expect(c.open).toHaveBeenCalledTimes(1);
});

test("Stop aborts the request, keeps the partial answer and ignores later chunks", async () => {
  const c = controlled();
  render(<AssistantPanel openStream={c.open} />);
  await ask();
  await act(async () => { c.push(META + tok(1, "For ") + tok(2, "two ")); });
  await waitFor(() => expect(log()).toHaveTextContent("For two"));
  expect(screen.getByRole("status")).toHaveTextContent(/typing/i);
  await userEvent.click(screen.getByRole("button", { name: "Stop" }));
  expect(c.signals[0].aborted).toBe(true);
  await act(async () => { c.push(tok(3, "people ")); });
  expect(log()).toHaveTextContent("For two");
  expect(log()).not.toHaveTextContent("people");
  expect(screen.getByRole("status")).toHaveTextContent("Stopped");
  expect(screen.queryByRole("alert")).toBeNull();
  expect(screen.queryByRole("button", { name: "Stop" })).toBeNull();
  await userEvent.type(screen.getByLabelText("Ask about products"), "again");
  expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();
});

test("a server error event shows its message; Try again re-sends the prompt and clears the old text", async () => {
  const c = controlled();
  render(<AssistantPanel openStream={c.open} />);
  await ask("where is order 1182?");
  await act(async () => { c.push(fixture("rate-limited.sse")); });
  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent("The assistant is handling a lot of questions. Please try again.");
  await userEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(c.open).toHaveBeenCalledTimes(2);
  expect(c.requests[1].prompt).toBe("where is order 1182?");
  expect(log()).not.toHaveTextContent("Let me check");
  expect(screen.queryByRole("alert")).toBeNull();
});

test("a connection that drops midway, or ends without done, is a retryable error", async () => {
  const c = controlled();
  render(<AssistantPanel openStream={c.open} />);
  await ask();
  await act(async () => { c.push(tok(1, "For ")); });
  await act(async () => { c.fail(new TypeError("network error")); });
  expect(await screen.findByRole("alert")).toHaveTextContent(MESSAGES.connectionLost);
  expect(log()).toHaveTextContent("For");
  await userEvent.click(screen.getByRole("button", { name: "Try again" }));
  await act(async () => { c.push(tok(1, "Hello ")); });
  await act(async () => { c.end(); });
  expect(await screen.findByRole("alert")).toHaveTextContent(MESSAGES.connectionLost);
});

test("HTTP 429 from the gateway shows the busy message with Try again", async () => {
  const open = jest.fn(() => ({
    [Symbol.asyncIterator]() {
      return { next: async (): Promise<IteratorResult<string>> => { throw new StreamHttpError(429); } };
    },
  }));
  render(<AssistantPanel openStream={open} />);
  await ask();
  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent(MESSAGES.busy);
  expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
});

test("conversation id from meta goes with the next request and to the handoff", async () => {
  const c = controlled();
  const onHandoff = jest.fn();
  render(<AssistantPanel openStream={c.open} onHandoff={onHandoff} />);
  await ask("first");
  await act(async () => { c.push(META + tok(1, "Sure.") + 'event: done\ndata: {"stop_reason": "end_turn"}\n\n'); });
  await waitFor(() => expect(screen.getByRole("button", { name: "Send" })).toBeDisabled());
  await ask("second");
  expect(c.requests[1].conversationId).toBe("c-7f3a91");
  await userEvent.click(screen.getByRole("button", { name: "Talk to a person" }));
  expect(onHandoff).toHaveBeenCalledWith("c-7f3a91");
});

test("unmounting while streaming aborts the request", async () => {
  const c = controlled();
  const { unmount } = render(<AssistantPanel openStream={c.open} />);
  await ask();
  await act(async () => { c.push(tok(1, "For ")); });
  unmount();
  expect(c.signals[0].aborted).toBe(true);
});

test("malformed and unknown events are skipped; a repeated product renders once", async () => {
  const c = controlled();
  render(<AssistantPanel openStream={c.open} />);
  await ask();
  const prod = 'event: product\ndata: {"sku": "KO-LAMP-1", "name": "Trail Lantern", "price_cents": 3450, "in_stock": true, "url": "/p/KO-LAMP-1"}\n\n';
  await act(async () => {
    c.push("event: product\ndata: {not json\n\n" + "event: thinking\ndata: {\"x\": 1}\n\n" + prod + tok(1, "Try the lantern.") + prod);
    c.push('event: done\ndata: {"stop_reason": "end_turn"}\n\n');
  });
  await waitFor(() => expect(log()).toHaveTextContent("Try the lantern."));
  expect(screen.getAllByRole("article", { name: "Trail Lantern" })).toHaveLength(1);
  expect(screen.getByRole("article", { name: "Trail Lantern" })).toHaveTextContent("$34.50");
  expect(screen.queryByRole("alert")).toBeNull();
});

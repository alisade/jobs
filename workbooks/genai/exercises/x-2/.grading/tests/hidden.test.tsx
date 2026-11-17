import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatPage } from "../../src/ChatPage";
import type { Conversation } from "../../src/types";
import { CONVERSATIONS, fakeClient, fakeShortcuts } from "../helpers";

const sw = (name: string) => userEvent.click(screen.getByRole("button", { name }));
const talk = () => userEvent.click(screen.getByRole("button", { name: "Talk to a person" }));

test("guard: first conversation via the button", async () => {
  const { client, calls } = fakeClient();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={fakeShortcuts().shortcuts} />);
  await talk();
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0].conversationId).toBe("c-101");
});

test("switch then button: new id and the new transcript", async () => {
  const { client, calls } = fakeClient();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={fakeShortcuts().shortcuts} />);
  await sw("Return a stove");
  await talk();
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0]).toEqual({
    conversationId: "c-102",
    transcript: [
      "customer: My camp stove leaks gas, order 1182.",
      "assistant: I am sorry. I can start a return for order 1182.",
      "customer: I want to talk to someone.",
    ],
  });
});

test("switch then Alt+H: new id", async () => {
  const { client, calls } = fakeClient();
  const sc = fakeShortcuts();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={sc.shortcuts} />);
  await sw("Return a stove");
  await act(async () => { sc.fire("alt+h"); });
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0].conversationId).toBe("c-102");
});

test("repeated switching: every handoff matches the conversation on screen", async () => {
  const { client, calls } = fakeClient();
  const sc = fakeShortcuts();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={sc.shortcuts} />);
  for (const [name, id] of [["Store hours", "c-103"], ["Tent for two", "c-101"], ["Return a stove", "c-102"]] as const) {
    await sw(name);
    await talk();
    await act(async () => { sc.fire("alt+h"); });
    await waitFor(() => expect(calls.length % 2).toBe(0));
    expect(calls.slice(-2).map((c) => c.conversationId)).toEqual([id, id]);
  }
});

test("a message that arrives after opening is included in the transcript", async () => {
  const { client, calls } = fakeClient();
  const sc = fakeShortcuts();
  const { rerender } = render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={sc.shortcuts} />);
  await sw("Return a stove");
  const updated: Conversation[] = CONVERSATIONS.map((c) =>
    c.id === "c-102" ? { ...c, messages: [...c.messages, { role: "assistant", text: "Connecting you now." }] } : c,
  );
  rerender(<ChatPage conversations={updated} client={client} shortcuts={sc.shortcuts} />);
  await act(async () => { sc.fire("alt+h"); });
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0].transcript[calls[0].transcript.length - 1]).toBe("assistant: Connecting you now.");
});

test("exactly one shortcut registration after many switches; one handoff per keypress", async () => {
  const { client, calls } = fakeClient();
  const sc = fakeShortcuts();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={sc.shortcuts} />);
  for (const name of ["Return a stove", "Store hours", "Tent for two", "Return a stove"]) await sw(name);
  expect(sc.active()).toBe(1);
  await act(async () => { sc.fire("alt+h"); });
  await waitFor(() => expect(calls).toHaveLength(1));
  await new Promise((r) => setTimeout(r, 20));
  expect(calls).toHaveLength(1);
  expect(calls[0].conversationId).toBe("c-102");
});

test("one click is one handoff", async () => {
  const { client, calls } = fakeClient();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={fakeShortcuts().shortcuts} />);
  await sw("Store hours");
  await talk();
  await waitFor(() => expect(calls).toHaveLength(1));
  await new Promise((r) => setTimeout(r, 20));
  expect(calls).toHaveLength(1);
});

test("guard: unmount removes the shortcut", async () => {
  const sc = fakeShortcuts();
  const { unmount } = render(<ChatPage conversations={CONVERSATIONS} client={fakeClient().client} shortcuts={sc.shortcuts} />);
  expect(sc.active()).toBe(1);
  unmount();
  expect(sc.active()).toBe(0);
});

test("a new client prop is used for the next handoff", async () => {
  const a = fakeClient();
  const b = fakeClient();
  const sc = fakeShortcuts();
  const { rerender } = render(<ChatPage conversations={CONVERSATIONS} client={a.client} shortcuts={sc.shortcuts} />);
  rerender(<ChatPage conversations={CONVERSATIONS} client={b.client} shortcuts={sc.shortcuts} />);
  await act(async () => { sc.fire("alt+h"); });
  await waitFor(() => expect(b.calls).toHaveLength(1));
  expect(a.calls).toHaveLength(0);
});

test("guard: a failed handoff shows the alert", async () => {
  const client = { handoff: jest.fn(async () => { throw new Error("503"); }) };
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={fakeShortcuts().shortcuts} />);
  await talk();
  expect(await screen.findByRole("alert")).toHaveTextContent("could not reach a person");
});

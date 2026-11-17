import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChatPage } from "../src/ChatPage";
import { CONVERSATIONS, fakeClient, fakeShortcuts } from "./helpers";

test("hands off the open conversation with its transcript", async () => {
  const { client, calls } = fakeClient();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={fakeShortcuts().shortcuts} />);
  await userEvent.click(screen.getByRole("button", { name: "Talk to a person" }));
  expect(await screen.findByRole("status")).toHaveTextContent("T-5001");
  expect(calls[0]).toEqual({
    conversationId: "c-101",
    transcript: ["customer: Do you have a tent for two under 2 kg?", "assistant: The Ridgeline 2P weighs 1.9 kg."],
  });
});

test("Alt+H hands off too", async () => {
  const { client, calls } = fakeClient();
  const sc = fakeShortcuts();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={sc.shortcuts} />);
  await act(async () => { sc.fire("alt+h"); });
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0].conversationId).toBe("c-101");
});

// Repro from SUP-7781: fails until the incident is fixed.
test("repro: after switching conversations, the handoff carries the new conversation", async () => {
  const { client, calls } = fakeClient();
  render(<ChatPage conversations={CONVERSATIONS} client={client} shortcuts={fakeShortcuts().shortcuts} />);
  await userEvent.click(screen.getByRole("button", { name: "Return a stove" }));
  await userEvent.click(screen.getByRole("button", { name: "Talk to a person" }));
  await waitFor(() => expect(calls).toHaveLength(1));
  expect(calls[0].conversationId).toBe("c-102");
});

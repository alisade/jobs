// Visible tests for connect/w7-c2. The grader adds more.
import React from "react";
import { render, screen } from "@testing-library/react";
import { FakeContactClient, appMod, guides, resetHandoff, fakeApi } from "./fakeWorkspace";

const noSuggestions = async () => [];

test("waits for a contact, then shows the bot handoff context", async () => {
  const client = new FakeContactClient();
  render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
  expect(screen.getByRole("status")).toHaveTextContent(/waiting/i);
  await client.connect("c-1", resetHandoff());
  expect(screen.getByTestId("summary")).toHaveTextContent(/locked out/);
  expect(screen.getByTestId("intent")).toHaveTextContent("ResetPassword");
  expect(screen.getByTestId("incident")).toHaveTextContent("INC0012345");
});

test("shows the password reset checklist for the ResetPassword intent", async () => {
  const client = new FakeContactClient();
  render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
  await client.connect("c-1", resetHandoff());
  expect(screen.getByText("Password reset")).toBeInTheDocument();
  expect(screen.getAllByRole("checkbox")).toHaveLength(5);
});

test("slots from the bot are listed", async () => {
  const client = new FakeContactClient();
  render(<appMod.AgentAssistApp client={client} api={fakeApi()} guides={guides} loadSuggestions={noSuggestions} />);
  await client.connect("c-1", resetHandoff());
  expect(screen.getByRole("list", { name: "Slots" })).toHaveTextContent("device: new phone");
});

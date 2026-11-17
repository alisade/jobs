import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssistantEntry } from "../src/AssistantEntry";
import { fakeFlags, fakeSearch, sink, controlled, META, tok, DONE } from "./helpers";

async function query(text: string) {
  await userEvent.type(screen.getByLabelText("Search Kestrel"), text);
  await userEvent.click(screen.getByRole("button", { name: "Search" }));
}

test("off: legacy results only, the assistant is never called", async () => {
  const flags = fakeFlags({ killSwitch: false, mode: "off", percent: 100 });
  const c = controlled();
  const search = fakeSearch();
  render(<AssistantEntry userId="cust-1" flags={flags.client} openStream={c.open} search={search} track={sink().track} />);
  await query("tent for two");
  expect(await screen.findByRole("list", { name: "Search results" })).toHaveTextContent("Ridgeline 2P Tent");
  expect(search).toHaveBeenCalledWith("tent for two");
  expect(c.open).not.toHaveBeenCalled();
});

test("on (100%): the assistant answer streams in", async () => {
  const flags = fakeFlags({ killSwitch: false, mode: "on", percent: 100 });
  const c = controlled();
  render(<AssistantEntry userId="cust-1" flags={flags.client} openStream={c.open} search={fakeSearch()} track={sink().track} />);
  await query("tent for two");
  await act(async () => { c.push(META + tok(1, "The Ridgeline 2P ") + tok(2, "fits two.") + DONE); });
  await waitFor(() => expect(screen.getByRole("log", { name: "Assistant answer" })).toHaveTextContent("The Ridgeline 2P fits two."));
  expect(c.requests[0].prompt).toBe("tent for two");
});

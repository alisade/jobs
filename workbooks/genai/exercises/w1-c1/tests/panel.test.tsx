import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AssistantPanel } from "../src/AssistantPanel";
import { fixture, eventChunks, replay } from "./helpers";

const FULL =
  "For two people on a weekend trip, the Ridgeline 2P is the best fit: it weighs 1.9 kg and packs small. " +
  "If you want more room, look at the Basecamp 3P.";

test("streams the recorded answer into the answer region", async () => {
  const open = replay(eventChunks(fixture("tent-question.sse")));
  render(<AssistantPanel openStream={open} />);
  await userEvent.type(screen.getByLabelText("Ask about products"), "tent for two?");
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
  const log = screen.getByRole("log", { name: "Assistant answer" });
  await screen.findByText(/Basecamp 3P\.$/);
  expect(log).toHaveTextContent(FULL);
  expect(open).toHaveBeenCalledTimes(1);
  expect(open.mock.calls[0][0].prompt).toBe("tent for two?");
});

test("shows the suggested products", async () => {
  render(<AssistantPanel openStream={replay(eventChunks(fixture("tent-question.sse")))} />);
  await userEvent.type(screen.getByLabelText("Ask about products"), "tent for two?");
  await userEvent.click(screen.getByRole("button", { name: "Send" }));
  expect(await screen.findByText("Ridgeline 2P Tent", { exact: false })).toBeInTheDocument();
});

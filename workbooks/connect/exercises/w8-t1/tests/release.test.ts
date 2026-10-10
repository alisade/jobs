// Visible tests for connect/w8-t1. The grader adds more.
import { checkRefs } from "../pipeline/check-refs";
import { prod, releaseArtifacts } from "./harness";

test("four prod artifacts exist and their content parses", () => {
  const a = releaseArtifacts();
  expect(a.map((x) => x.name)).toEqual(["mod-after-hours", "mod-password-reset", "LFG Help Desk Inbound", "LFG Major Incident"]);
  for (const x of a) expect(() => JSON.parse(x.content)).not.toThrow();
});

test("queues in the major-incident flow point at prod", () => {
  const inv = prod();
  const major = JSON.parse(releaseArtifacts().find((x) => x.name === "LFG Major Incident")!.content);
  const q = inv.resources.find((r) => r.kind === "queue" && r.name === "MajorIncident")!.arn;
  expect(major.Actions[0].Parameters.QueueId).toBe(q);
});

test("check-refs flags a prompt that does not exist in the target", () => {
  const inv = prod();
  const content = JSON.stringify({ Version: "2019-10-30", StartAction: "a", Actions: [
    { Identifier: "a", Type: "MessageParticipant", Parameters: { PromptId: `${inv.instanceArn}/prompt/00000000-0000-4000-8000-000000000000` }, Transitions: {} },
  ] });
  const p = checkRefs("t", content, inv);
  expect(p).toHaveLength(1);
  expect(p[0].reason).toBe("not-in-target-inventory");
  expect(p[0].path).toBe("$.Actions[0].Parameters.PromptId");
});

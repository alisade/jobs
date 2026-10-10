// Hidden tests for connect/w1-t1: the fixed flow, plus guards against regressions.
import { validateFlow } from "connect-kit";
import { call, loadFlow, Q } from "../harness";

const flow = loadFlow();

test("lint is clean (no errors of any kind)", () => {
  expect(validateFlow(flow).issues.filter((i) => i.severity === "error")).toEqual([]);
});

test("no staffing check is pinned to the PasswordReset queue", () => {
  const pinned = flow.Actions.filter((a) => a.Type === "CheckMetricData" && a.Parameters.QueueId === Q.PasswordReset);
  expect(pinned).toEqual([]);
});

test("option 2 with PasswordReset unstaffed: straight to GeneralSupport, no busy message", () => {
  const r = call({ option: "2", staffed: { PasswordReset: 0 } });
  expect(r.queueName).toBe("GeneralSupport");
  expect(r.prompts.join(" ")).not.toMatch(/busy/i);
});

test("VIP caller is not overflowed because a different team is unstaffed", () => {
  const r = call({ vip: true, staffed: { PasswordReset: 0 } });
  expect(r.queueName).toBe("VIPDesk");
});

test("outage report with PasswordReset unstaffed reaches MajorIncident", () => {
  const r = call({ option: "3", staffed: { PasswordReset: 0 } });
  expect(r.queueName).toBe("MajorIncident");
});

test("failed self-service reset with PasswordReset unstaffed overflows once to GeneralSupport", () => {
  const r = call({ option: "1", reset: "FAILED", staffed: { PasswordReset: 0 } });
  expect(r.outcome).toBe("TransferredToQueue");
  expect(r.queueName).toBe("GeneralSupport");
  expect(r.prompts.filter((p) => /busy/i.test(p))).toHaveLength(1);
});

test("nobody staffed anywhere: the caller gets a message and a clean disconnect, never a loop", () => {
  const r = call({ option: "1", reset: "FAILED", staffed: { PasswordReset: 0, GeneralSupport: 0, VIPDesk: 0, MajorIncident: 0 } });
  expect(r.outcome).not.toBe("StepLimit");
  expect(["Disconnected", "TransferredToQueue"]).toContain(r.outcome);
  expect(r.steps).toBeLessThan(40);
});

test("VIP with VIPDesk unstaffed overflows to GeneralSupport", () => {
  const r = call({ vip: true, staffed: { VIPDesk: 0 } });
  expect(r.queueName).toBe("GeneralSupport");
});

test("guard: everyone staffed, failed reset goes to PasswordReset", () => {
  const r = call({ option: "1", reset: "FAILED" });
  expect(r.queueName).toBe("PasswordReset");
});

test("guard: successful reset still self-serves", () => {
  const r = call({ option: "1", reset: "SENT" });
  expect(r.outcome).toBe("Disconnected");
  expect(r.prompts.join(" ")).toMatch(/reset link/i);
});

test("guard: the overflow intent of CHG-48211 is kept (no caller is sent to an empty GeneralSupport queue)", () => {
  const r = call({ option: "1", reset: "FAILED", staffed: { PasswordReset: 0, GeneralSupport: 0 } });
  expect(r.queueName === "GeneralSupport" && r.outcome === "TransferredToQueue").toBe(false);
});

test("every scenario terminates for every staffing combination", () => {
  const names = ["GeneralSupport", "PasswordReset", "VIPDesk", "MajorIncident"];
  for (let mask = 0; mask < 16; mask++) {
    const staffed = Object.fromEntries(names.map((n, i) => [n, mask & (1 << i) ? 2 : 0]));
    for (const option of ["1", "2", "3"]) {
      for (const vip of [false, true]) {
        const r = call({ option, vip, staffed, reset: "FAILED" });
        expect(r.outcome === "StepLimit" ? `${option}/${vip}/${mask}` : "ok").toBe("ok");
      }
    }
  }
});

// Visible tests for connect/x-1. The grader adds more.
import { createHandler } from "../src/handler";
import { event, fakeSn, fastSleep, incidents } from "./harness";

test("creates one incident carrying the contact id and returns its number", async () => {
  const { sn, client } = await fakeSn();
  try {
    const out = await createHandler({ sn: client, sleep: fastSleep })(event("c-0001"));
    expect(out.error).toBe("");
    expect(out.incidentNumber).toMatch(/^INC\d{7}$/);
    const rows = incidents(sn, "c-0001");
    expect(rows).toHaveLength(1);
    expect(rows[0].contact_type).toBe("phone");
  } finally {
    await sn.stop();
  }
});

test("different contacts get different incidents", async () => {
  const { sn, client } = await fakeSn();
  try {
    const h = createHandler({ sn: client, sleep: fastSleep });
    const a = await h(event("c-0002"));
    const b = await h(event("c-0003", "CHAT"));
    expect(a.incidentNumber).not.toBe(b.incidentNumber);
    expect(incidents(sn, "c-0003")[0].contact_type).toBe("chat");
  } finally {
    await sn.stop();
  }
});

test("the OAuth token is reused across invocations", async () => {
  const { sn, client } = await fakeSn();
  try {
    const h = createHandler({ sn: client, sleep: fastSleep });
    await h(event("c-0004"));
    await h(event("c-0005"));
    expect(sn.counters.token).toBe(1);
  } finally {
    await sn.stop();
  }
});

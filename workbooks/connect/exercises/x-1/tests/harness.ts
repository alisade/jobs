// Fixtures for the x-1 tests: a fake ServiceNow (connect-kit) and Connect events.
import { startFakeServiceNow, FakeServiceNow } from "connect-kit";
import { ServiceNowClient } from "../src/servicenow";

export const fastSleep = (ms: number) => new Promise<void>((r) => setTimeout(r, Math.min(ms, 40)));

export async function fakeSn(faults: FakeServiceNow["faults"] = {}): Promise<{ sn: FakeServiceNow; client: ServiceNowClient }> {
  const sn = await startFakeServiceNow({ faults: { retryAfterSeconds: 0, ...faults } });
  const client = new ServiceNowClient({ baseUrl: sn.url, clientId: sn.client.clientId, clientSecret: sn.client.clientSecret, timeoutMs: 2000, maxRetries: 2, sleep: fastSleep });
  return { sn, client };
}

export function event(contactId: string, channel = "VOICE") {
  return {
    Name: "ContactFlowEvent",
    Details: {
      ContactData: { ContactId: contactId, InitialContactId: contactId, Channel: channel, Attributes: { employeeSysId: "62826bf03710200044e0bfc8bcbe5df1", employeeId: "E10442" } },
      Parameters: { shortDescription: "Cannot connect to GlobalProtect VPN", category: "network", description: "Bot summary: VPN error 'gateway unreachable' since this morning." },
    },
  };
}

export const incidents = (sn: FakeServiceNow, contactId: string) => (sn.db.incident || []).filter((r) => r.correlation_id === contactId);

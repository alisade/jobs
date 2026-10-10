// lfg-servicenow-incident: invoked from the help desk inbound flow (Invoke AWS Lambda function,
// synchronous, STRING_MAP response). See README.md for the contract.
import type { ConnectContactFlowEvent } from "aws-lambda";
import { CustomerProfilesClient, SearchProfilesCommand } from "@aws-sdk/client-customer-profiles";
import { Clock, ServiceNowClient, realClock } from "./servicenow";

export type Deps = {
  profiles: CustomerProfilesClient;
  domainName: string;
  sn: ServiceNowClient;
  clock?: Clock;
  budgetMs?: number;
};

type SysUser = { sys_id: string; user_name: string; employee_number: string; vip: string };
type Incident = { sys_id: string; number: string; short_description: string; correlation_id: string; state: string };

export type FlowResponse = Record<string, any>;

export function makeHandler(deps: Deps) {
  const clock = deps.clock ?? realClock;
  const budgetMs = deps.budgetMs ?? 6500;
  return async (event: ConnectContactFlowEvent): Promise<FlowResponse> => {
    const deadline = clock.now() + budgetMs;
    const contact = event.Details.ContactData;
    const params = (event.Details.Parameters || {}) as Record<string, string>;
    const phone = contact.CustomerEndpoint!.Address;

    const found = await deps.profiles.send(new SearchProfilesCommand({ DomainName: deps.domainName, KeyName: "_phone", Values: [phone] }));
    const employeeNumber = found.Items?.[0]?.AccountNumber;
    if (!employeeNumber) return { status: "NOT_FOUND", employeeFound: "false" };

    const users = await deps.sn.listAll<SysUser>("sys_user", `employee_number=${employeeNumber}`, ["sys_id", "user_name", "employee_number", "vip"], deadline);
    const user = users[0];
    const open = await deps.sn.listAll<Incident>("incident", `caller_id=${user.sys_id}^active=true^ORDERBYDESCsys_created_on`, ["sys_id", "number", "short_description", "correlation_id", "state"], deadline);

    // TODO: idempotency - Connect may invoke this more than once for the same contact.
    const created = await deps.sn.create<Incident>(
      "incident",
      {
        caller_id: user.sys_id,
        short_description: params.shortDescription || "Help desk call",
        category: params.category || "inquiry",
        contact_type: "phone",
      },
      deadline,
    );
    return {
      status: "OK",
      employeeFound: true,
      employeeId: employeeNumber,
      vip: user.vip,
      openIncidentCount: open.length + 1,
      latestOpenIncident: open[0]?.number || "",
      incidentCreated: true,
      incidentNumber: created.number,
      incidentSysId: created.sys_id,
    };
  };
}

let cached: ((e: ConnectContactFlowEvent) => Promise<FlowResponse>) | null = null;
export const handler = async (event: ConnectContactFlowEvent): Promise<FlowResponse> => {
  if (!cached) {
    cached = makeHandler({
      profiles: new CustomerProfilesClient({}),
      domainName: process.env.PROFILES_DOMAIN || "lfg-employees",
      sn: new ServiceNowClient({
        baseUrl: process.env.SN_BASE_URL || "https://larkspur.service-now.com",
        clientId: process.env.SN_CLIENT_ID || "",
        clientSecret: process.env.SN_CLIENT_SECRET || "",
      }),
    });
  }
  return cached(event);
};

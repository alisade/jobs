// Backend for the workspace app: a small REST API (API Gateway + Lambda in production) that
// updates the ServiceNow incident on the agent's behalf. The app never talks to ServiceNow directly.

export type IncidentUpdate = { work_notes: string; state?: string; close_code?: string; close_notes?: string };

export interface IncidentApi {
  updateIncident(sysId: string, update: IncidentUpdate): Promise<{ number: string; state: string }>;
}

export function createIncidentApi(baseUrl: string, getToken: () => Promise<string>, fetchImpl: typeof fetch = fetch): IncidentApi {
  return {
    async updateIncident(sysId, update) {
      if (!/^[a-f0-9]{32}$/.test(sysId)) throw new Error("invalid incident sys_id");
      const res = await fetchImpl(`${baseUrl}/incidents/${encodeURIComponent(sysId)}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${await getToken()}` },
        body: JSON.stringify(update),
      });
      if (!res.ok) throw new Error(`incident update failed (${res.status})`);
      return (await res.json()) as { number: string; state: string };
    },
  };
}

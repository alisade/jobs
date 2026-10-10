// Small builders for hand-made routing scenarios.
import { Agent, Contact, RoutingProfile, SimConfig } from "../src/types";

export const contact = (id: string, queueId: string, arrival: number, handleSeconds = 100, patienceSeconds = 10000, extra: Partial<Contact> = {}): Contact => ({
  id, queueId, arrival, handleSeconds, patienceSeconds, ...extra,
});

export function config(profiles: RoutingProfile[], agents: Agent[], queues = ["q1", "q2"], threshold = 20): SimConfig {
  return { queues: queues.map((id) => ({ id })), routingProfiles: profiles, agents, serviceLevelThresholdSeconds: threshold };
}

export const outcome = (r: { contacts: { id: string }[] }, id: string) => (r.contacts as any[]).find((c) => c.id === id);

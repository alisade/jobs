// POST /v1/opportunities/:id/transitions  (pipeline-svc)
// Moves an opportunity to a new stage. See README.md for the contract.
import { randomUUID } from "crypto";
import type { FastifyInstance } from "fastify";
import type { AppOptions } from "./app";
import type { Stage } from "./types";

// Allowed stage graph (sales ops, 2026-10). Closed stages are terminal.
export const ALLOWED: Record<Stage, Stage[]> = {
  prospecting: ["qualification", "closed_lost"],
  qualification: ["proposal", "closed_lost"],
  proposal: ["negotiation", "qualification", "closed_lost"],
  negotiation: ["closed_won", "closed_lost", "proposal"],
  closed_won: [],
  closed_lost: [],
};

export function registerTransitions(app: FastifyInstance, opts: AppOptions): void {
  const { db } = opts.db;

  app.post<{ Params: { id: string } }>("/v1/opportunities/:id/transitions", async (req, reply) => {
    // First cut from the CRM port. It works on the happy path in the demo. TODO: everything in the README.
    const body = req.body as { to_stage: Stage; expected_version: number };
    const id = Number(req.params.id);
    const opp = await db.selectFrom("opportunities").selectAll().where("id", "=", id).executeTakeFirst();
    if (!opp) return reply.code(404).send({ error: "not found" });

    await db.updateTable("opportunities").set({ stage: body.to_stage, version: opp.version + 1 }).where("id", "=", id).execute();

    const eventId = randomUUID();
    await db.insertInto("outbox").values({
      event_id: eventId,
      tenant_id: opp.tenant_id,
      aggregate_type: "opportunity",
      aggregate_id: String(id),
      type: "OpportunityStageChanged",
      payload: JSON.stringify({ opportunity_id: id, to_stage: body.to_stage }),
      published_at: null,
    }).execute();

    return { id, stage: body.to_stage, version: opp.version + 1, event_id: eventId };
  });
}

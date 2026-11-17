// pipeline-svc HTTP app (Fastify). buildApp() is used by the server and by the tests (fastify.inject).
import Fastify, { FastifyInstance, FastifyError } from "fastify";
import type { Db } from "./db";
import { withTenant } from "./db";
import { registerTransitions } from "./transitions";
import { ProblemError, sendProblem } from "./problems";

export interface Hooks {
  // Test seams: called inside the transition transaction. Production passes nothing.
  afterLock?: () => Promise<void>;
  beforeCommit?: () => Promise<void>;
}

export interface AppOptions { db: Db; hooks?: Hooks }

declare module "fastify" {
  interface FastifyInstance { draining: boolean }
}

export function buildApp(opts: AppOptions): FastifyInstance {
  const app = Fastify({ logger: false });
  app.decorate("draining", false);

  app.setErrorHandler((err: FastifyError, req, reply) => {
    if (err instanceof ProblemError) return sendProblem(req, reply, err);
    const status = err.statusCode && err.statusCode >= 400 && err.statusCode < 500 ? err.statusCode : 500;
    if (status === 500) req.log.error({ err }, "unhandled error");
    return sendProblem(req, reply, status === 500
      ? new ProblemError(500, "internal", "Internal error", "The request failed; it was not applied.")
      : new ProblemError(status, "validation-error", "Request is invalid", err.message));
  });
  app.setNotFoundHandler((req, reply) =>
    sendProblem(req, reply, new ProblemError(404, "not-found", "Not found", `No route ${req.method} ${req.url}`)));

  app.get("/readyz", async (_req, reply) => {
    if (app.draining) return reply.code(503).send({ ready: false });
    return { ready: true };
  });

  app.get<{ Params: { id: string } }>("/v1/opportunities/:id", async (req) => {
    const tenant = req.headers["x-tenant-id"];
    if (typeof tenant !== "string" || !tenant) throw new ProblemError(400, "missing-tenant", "X-Tenant-Id header is required");
    const row = await withTenant(opts.db.db, tenant, (trx) =>
      trx.selectFrom("opportunities").selectAll().where("id", "=", Number(req.params.id)).executeTakeFirst());
    if (!row) throw new ProblemError(404, "not-found", "Opportunity not found");
    return row;
  });

  registerTransitions(app, opts);
  return app;
}

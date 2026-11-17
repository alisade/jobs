// Graceful shutdown for pipeline-svc pods. On SIGTERM: report not-ready (so endpoints drop the pod),
// refuse new work with 503, let in-flight requests finish, close the app (and the DB pool), exit 0.
// Exit 1 if draining takes longer than timeoutMs (better than being SIGKILLed mid-write).
import type { FastifyInstance } from "fastify";
import { ProblemError, sendProblem } from "./problems";

export interface ShutdownOptions {
  signals?: NodeJS.EventEmitter;
  exit?: (code: number) => void;
  timeoutMs?: number;
}

export function installGracefulShutdown(app: FastifyInstance, opts: ShutdownOptions = {}): void {
  const signals = opts.signals || process;
  const exit = opts.exit || ((code: number) => process.exit(code));
  const timeoutMs = opts.timeoutMs ?? 20000;
  let inFlight = 0;
  let started = false;

  const counted = new WeakSet<object>();
  app.addHook("onRequest", async (req, reply) => {
    if (req.url === "/readyz") return;
    if (app.draining) {
      reply.header("connection", "close").header("retry-after", "1");
      return sendProblem(req, reply, new ProblemError(503, "shutting-down", "Instance is shutting down", "Retry the request."));
    }
    inFlight += 1;
    counted.add(req);
  });
  app.addHook("onResponse", async (req) => {
    if (counted.has(req)) { counted.delete(req); inFlight -= 1; }
  });

  signals.on("SIGTERM", () => {
    if (started) return;
    started = true;
    app.draining = true;
    const deadline = Date.now() + timeoutMs;
    const tick = async (): Promise<void> => {
      if (inFlight > 0 && Date.now() < deadline) { setTimeout(tick, 10); return; }
      const clean = inFlight === 0;
      try { await app.close(); } catch { /* closing anyway */ }
      exit(clean ? 0 : 1);
    };
    void tick();
  });
}

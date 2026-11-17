// Graceful shutdown for pipeline-svc pods. Kubernetes sends SIGTERM, keeps routing traffic to the pod
// for a few seconds while endpoints update, then SIGKILLs after terminationGracePeriodSeconds.
import type { FastifyInstance } from "fastify";

export interface ShutdownOptions {
  signals?: NodeJS.EventEmitter;      // default: process
  exit?: (code: number) => void;      // default: process.exit
  timeoutMs?: number;                 // give up draining after this long (default 20000)
}

export function installGracefulShutdown(app: FastifyInstance, opts: ShutdownOptions = {}): void {
  const signals = opts.signals || process;
  const exit = opts.exit || ((code: number) => process.exit(code));
  // TODO: drain instead of dying (README "Graceful shutdown").
  signals.on("SIGTERM", () => {
    exit(0);
  });
}

// RFC 9457 problem details for pipeline-svc. Every error response is application/problem+json.
import type { FastifyReply, FastifyRequest } from "fastify";

export const PROBLEM_BASE = "https://keystone.lumenfold.example/problems/";

export class ProblemError extends Error {
  constructor(
    public readonly status: number,
    public readonly slug: string,
    public readonly title: string,
    public readonly detail?: string,
    public readonly extra: Record<string, unknown> = {},
  ) {
    super(detail || title);
  }
}

export function sendProblem(req: FastifyRequest, reply: FastifyReply, p: ProblemError): FastifyReply {
  return reply
    .code(p.status)
    .type("application/problem+json")
    .send({ type: PROBLEM_BASE + p.slug, title: p.title, status: p.status, detail: p.detail, instance: req.url, ...p.extra });
}

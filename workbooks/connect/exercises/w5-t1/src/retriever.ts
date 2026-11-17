// Help desk retriever (contact center team): builds the entitlement filter and calls Retrieve.
import { Entitlements, Filter, RetrievalOutcome, RetrieveFn, RetrieveInput } from "./types";

export const KB_ID = "KBLFGHELP01";

export function buildFilter(e: Entitlements): Filter {
  if (!e.callerVerified) {
    return { andAll: [{ equals: { key: "audience", value: "public-help" } }, { equals: { key: "status", value: "published" } }] };
  }
  const audience: Filter =
    e.employeeType === "contractor"
      ? { in: { key: "audience", value: ["all-workers", "contractors"] } }
      : { orAll: [{ in: { key: "audience", value: ["all-workers", "all-employees"] } }, { equals: { key: "department", value: e.department } }] };
  return {
    andAll: [audience, { in: { key: "region", value: ["global", e.region.toLowerCase()] } }, { equals: { key: "status", value: "published" } }],
  };
}

export async function retrieve(retrieveFn: RetrieveFn, query: string, who: Entitlements, numberOfResults = 3): Promise<RetrievalOutcome> {
  const input: RetrieveInput = {
    knowledgeBaseId: KB_ID,
    retrievalQuery: { text: query },
    retrievalConfiguration: { vectorSearchConfiguration: { numberOfResults, filter: buildFilter(who) } },
  };
  const first = await retrieveFn(input);
  const log: Record<string, unknown> = { query, filter: input.retrievalConfiguration.vectorSearchConfiguration.filter, filteredCount: first.retrievalResults.length, fallback: null };
  if (first.retrievalResults.length > 0) return { status: "OK", results: first.retrievalResults, log };
  // HD-2231 (2026.09.22): widen the search when the filter finds nothing, to improve containment.
  const widened = await retrieveFn({ ...input, retrievalConfiguration: { vectorSearchConfiguration: { numberOfResults } } });
  log.fallback = "unfiltered";
  if (widened.retrievalResults.length > 0) return { status: "OK", results: widened.retrievalResults, log };
  return { status: "NO_ARTICLES", results: [], log };
}

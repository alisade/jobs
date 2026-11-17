// Contract between the Connect flow, this Lambda and the agent workspace.

/** Who is asking, taken from contact attributes the flow set from a server-side directory lookup.
 *  Never from caller speech or model output. */
export type Entitlements = {
  callerVerified: boolean;
  department: string; // e.g. "Finance"
  region: string; // "us" | "uk" | "in" | "mx"
  employeeType: "employee" | "contractor";
};

export type RagConfig = {
  knowledgeBaseId: string;
  modelId: string;
  guardrailIdentifier: string;
  guardrailVersion: string;
  numberOfResults: number;
  minScore: number;
  searchType: "HYBRID" | "SEMANTIC";
  budgetMs: number;
  retrieveTimeoutMs: number;
  maxTokens: number;
};

export type HandoffReason =
  | "NOT_VERIFIED_NO_ARTICLES"
  | "NO_RELEVANT_ARTICLES"
  | "MODEL_DECLINED"
  | "GUARDRAIL_INTERVENED"
  | "UNCITED"
  | "BAD_CITATION"
  | "TIMEOUT"
  | "RETRIEVAL_ERROR"
  | "MODEL_ERROR"
  | "EMPTY_QUESTION";

export type AnswerResult =
  | { status: "ANSWERED"; answer: string; citations: string[]; latencyMs: number }
  | { status: "HANDOFF"; reason: HandoffReason; detail?: string; latencyMs: number };

/** The flat STRING_MAP the Connect flow reads as $.External.<key>. */
export type ConnectResult = Record<string, string>;

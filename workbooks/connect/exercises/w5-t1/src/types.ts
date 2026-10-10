export type Entitlements = { callerVerified: boolean; department: string; region: string; employeeType: "employee" | "contractor" };

/** ServiceNow kb_knowledge record (Table API export, fields used here). */
export type SnArticle = {
  sys_id: string; number: string; short_description: string; text: string;
  u_department: string; u_audience: string; u_region: string; workflow_state: "published" | "retired" | "draft";
  sys_updated_on: string; kb_knowledge_base: string;
};

/** An S3 object for the knowledge base data source plus its <key>.metadata.json sidecar. */
export type KbObject = { key: string; body: string; sidecar: { metadataAttributes: Record<string, string> } };

/** Bedrock Retrieve filter subset used by LFG (andAll/orAll/equals/in). */
export type Filter =
  | { andAll: Filter[] } | { orAll: Filter[] }
  | { equals: { key: string; value: string } } | { in: { key: string; value: string[] } };

export type RetrieveInput = { knowledgeBaseId: string; retrievalQuery: { text: string }; retrievalConfiguration: { vectorSearchConfiguration: { numberOfResults: number; filter?: Filter } } };
export type RetrieveOutput = { retrievalResults: { content: { text: string }; location: { type: "S3"; s3Location: { uri: string } }; metadata: Record<string, string>; score: number }[] };
export type RetrieveFn = (input: RetrieveInput) => Promise<RetrieveOutput>;

export type RetrievalOutcome =
  | { status: "OK"; results: RetrieveOutput["retrievalResults"]; log: Record<string, unknown> }
  | { status: "NO_ARTICLES"; results: []; log: Record<string, unknown> };

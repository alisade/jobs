// Shapes used by the promotion tool. The export files are what DescribeContactFlow /
// DescribeContactFlowModule return (Content is a JSON *string*, exactly as the API returns it).

export type ResourceKind = "queue" | "hours" | "prompt" | "lambda" | "lexAlias" | "module" | "flow";

export interface Resource {
  kind: ResourceKind;
  /** logical name, identical in every environment: the join key for promotion */
  name: string;
  arn: string;
  /** Connect resource id (the last ARN segment) for Connect resources; absent for Lambda / Lex */
  id?: string;
}

/** One environment's inventory (dev export inventory, or a target environment manifest). */
export interface Inventory {
  env: string;
  accountId: string;
  region: string;
  instanceId: string;
  instanceArn: string;
  resources: Resource[];
}

export interface ContactFlowExport {
  ContactFlow: { Arn: string; Id: string; Name: string; Type: string; State: string; Status: string; Description?: string; Content: string };
}
export interface ModuleExport {
  ContactFlowModule: { Arn: string; Id: string; Name: string; State: string; Status: string; Content: string };
}

export interface DevExport {
  inventory: Inventory;
  flows: ContactFlowExport[];
  modules: ModuleExport[];
}

/** A deployable artifact: the input for CreateContactFlow / UpdateContactFlowContent (or the module equivalents). */
export interface Artifact {
  kind: "module" | "flow";
  name: string;
  /** contact flow type (CONTACT_FLOW, CUSTOMER_QUEUE, ...); undefined for modules */
  type?: string;
  /** id/ARN of the same-named flow or module in the target environment, null if it does not exist there yet */
  targetId: string | null;
  targetArn: string | null;
  /** rewritten flow-language JSON, serialized (as the API expects) */
  content: string;
}

export interface Replacement {
  artifact: string;
  /** JSONPath-like location inside the parsed Content, e.g. $.Actions[3].Parameters.QueueId */
  path: string;
  from: string;
  to: string;
  /** "<kind>:<logical name>", or "instance" for the instance ARN / id */
  resource: string;
}

export type ProblemReason = "unknown-reference" | "unmapped-in-target" | "dangling";

export interface Problem {
  artifact: string;
  path: string;
  value: string;
  reason: ProblemReason;
  detail: string;
}

export interface PromotionResult {
  ok: boolean;
  artifacts: Artifact[];
  replacements: Replacement[];
  problems: Problem[];
}

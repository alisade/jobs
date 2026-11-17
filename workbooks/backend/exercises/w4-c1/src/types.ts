// Kysely table types for pipeline-svc.
import type { Generated, ColumnType } from "kysely";

export const STAGES = ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"] as const;
export type Stage = (typeof STAGES)[number];

export interface OpportunityTable {
  id: Generated<number>;
  tenant_id: string;
  account_id: number;
  owner_id: string;
  name: string;
  stage: Stage;
  amount: ColumnType<string | number, string | number | undefined, string | number>;
  close_date: ColumnType<Date | null, string | null | undefined, string | null>;
  version: Generated<number>;
  updated_at: Generated<Date>;
}

export interface StageHistoryTable {
  id: Generated<number>;
  tenant_id: string;
  opportunity_id: number;
  from_stage: Stage;
  to_stage: Stage;
  version: number;
  changed_by: string;
  changed_at: Generated<Date>;
}

export interface OutboxTable {
  event_id: string;
  tenant_id: string;
  aggregate_type: string;
  aggregate_id: string;
  type: string;
  payload: unknown;
  created_at: Generated<Date>;
  published_at: Date | null;
}

export interface Database {
  opportunities: OpportunityTable;
  stage_history: StageHistoryTable;
  outbox: OutboxTable;
}

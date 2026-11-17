// TODO (learner): translate a Cisco ICM/CVP routing script (simplified XML export) into an
// equivalent Amazon Connect flow. Use parseIcm() from ../legacy/cisco.
import type { Flow } from "connect-kit";
import { parseIcm } from "../legacy/cisco";
import { Mapping } from "../types";
import { FlowBuilder } from "../flowBuilder";

export function translateCisco(source: string, m: Mapping): Flow {
  const script = parseIcm(source);
  void script; void m; void FlowBuilder;
  throw new Error("translateCisco: not implemented");
}

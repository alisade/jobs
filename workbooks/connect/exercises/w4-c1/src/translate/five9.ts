// TODO (learner): translate a Five9 IVR script (simplified XML export) into an equivalent Amazon
// Connect flow. Use parseFive9() from ../legacy/five9.
import type { Flow } from "connect-kit";
import { parseFive9 } from "../legacy/five9";
import { Mapping } from "../types";
import { FlowBuilder } from "../flowBuilder";

export function translateFive9(source: string, m: Mapping): Flow {
  const script = parseFive9(source);
  void script; void m; void FlowBuilder;
  throw new Error("translateFive9: not implemented");
}

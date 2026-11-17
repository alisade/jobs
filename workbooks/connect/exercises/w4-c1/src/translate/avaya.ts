// TODO (learner): translate an Avaya CM call vector (text export) into an equivalent Amazon Connect
// flow (flow language 2019-10-30). Use parseVector() from ../legacy/avaya for the parsing; the
// mapping file tells you which Connect queue, hours, flow and prompt text each legacy name maps to.
// The README lists the semantics each step must keep.
import type { Flow } from "connect-kit";
import { parseVector } from "../legacy/avaya";
import { Mapping } from "../types";
import { FlowBuilder } from "../flowBuilder";

export function translateAvaya(source: string, m: Mapping): Flow {
  const vector = parseVector(source);
  void vector; void m; void FlowBuilder;
  throw new Error("translateAvaya: not implemented");
}

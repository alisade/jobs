// Tiny helper for emitting Connect flow-language JSON (provided; use it or not).
import type { Flow, FlowAction } from "connect-kit";

export type Transitions = FlowAction["Transitions"];

export class FlowBuilder {
  private actions: FlowAction[] = [];
  private used = new Set<string>();

  /** Reserve a readable unique Identifier (<= 50 chars, no forbidden characters). */
  id(base: string): string {
    const clean = base.replace(/[^A-Za-z0-9_\-]/g, "-").slice(0, 44) || "a";
    let id = clean;
    for (let i = 2; this.used.has(id); i++) id = `${clean}-${i}`;
    this.used.add(id);
    return id;
  }

  /** Add an action. Pass an Identifier from id() when something must point at it before it exists. */
  add(type: string, parameters: Record<string, any>, transitions: Transitions, identifier?: string): string {
    const Identifier = identifier || this.id(type);
    this.used.add(Identifier);
    this.actions.push({ Identifier, Type: type, Parameters: parameters, Transitions: transitions });
    return Identifier;
  }

  /** Same-target error list helper: errors(["NoMatchingError"], "x") */
  static errors(types: string[], to: string): { ErrorType: string; NextAction: string }[] {
    return types.map((ErrorType) => ({ ErrorType, NextAction: to }));
  }

  build(startAction: string, name: string): Flow {
    return { Version: "2019-10-30", StartAction: startAction, Metadata: { name, generatedBy: "lfg-legacy-translator" }, Actions: this.actions };
  }
}

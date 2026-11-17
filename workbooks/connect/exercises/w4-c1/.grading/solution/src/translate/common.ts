// Shared emitters used by the three translators: every Connect construct the legacy steps map to,
// with all required error branches wired (lint clean by construction).
import { FlowBuilder } from "../flowBuilder";

const ERR = FlowBuilder.errors;

export class Emitter {
  readonly b = new FlowBuilder();
  readonly disconnect: string;

  constructor() {
    this.disconnect = this.b.id("disconnect");
    this.b.add("DisconnectParticipant", {}, {}, this.disconnect);
  }

  /** Play a prompt, then continue (a prompt failure must not drop the caller). */
  message(text: string, next: string, id?: string): string {
    return this.b.add("MessageParticipant", { Text: text }, { NextAction: next, Errors: ERR(["NoMatchingError"], next) }, id);
  }

  /** CheckHoursOfOperation: open/closed branches; an error is treated as open. */
  hours(hoursArn: string, open: string, closed: string, id?: string): string {
    if (!hoursArn) throw new Error("hours resource missing from mapping");
    return this.b.add(
      "CheckHoursOfOperation",
      { HoursOfOperationId: hoursArn },
      {
        Conditions: [
          { NextAction: open, Condition: { Operator: "Equals", Operands: ["True"] } },
          { NextAction: closed, Condition: { Operator: "Equals", Operands: ["False"] } },
        ],
        Errors: ERR(["NoMatchingError"], open),
      },
      id,
    );
  }

  /** Collect one entry into a contact attribute; no input -> onNoInput (attribute cleared first if asked). */
  collect(text: string, attribute: string, next: string, onNoInput: string, id?: string): string {
    const set = this.b.id(`set-${attribute}`);
    const entry = this.b.add(
      "GetParticipantInput",
      { Text: text, StoreInput: "True", InputTimeLimitSeconds: "5" },
      { NextAction: set, Errors: ERR(["InputTimeLimitExceeded", "NoMatchingCondition", "NoMatchingError"], onNoInput) },
      id,
    );
    this.b.add("UpdateContactAttributes", { Attributes: { [attribute]: "$.StoredCustomerInput" }, TargetContact: "Current" }, { NextAction: next, Errors: ERR(["NoMatchingError"], next) }, set);
    return entry;
  }

  setAttributes(attrs: Record<string, string>, next: string, id?: string): string {
    return this.b.add("UpdateContactAttributes", { Attributes: attrs, TargetContact: "Current" }, { NextAction: next, Errors: ERR(["NoMatchingError"], next) }, id);
  }

  compareEquals(ref: string, value: string, onTrue: string, onFalse: string, id?: string): string {
    return this.b.add(
      "Compare",
      { ComparisonValue: ref },
      { Conditions: [{ NextAction: onTrue, Condition: { Operator: "Equals", Operands: [value] } }], Errors: ERR(["NoMatchingCondition"], onFalse) },
      id,
    );
  }

  /** Set working queue -> agents check -> priority -> transfer; any failure continues at onFail. */
  queue(queueArn: string, priority: number, metric: "NumberOfAgentsStaffed" | "NumberOfAgentsAvailable", onFail: string, id?: string): string {
    if (!queueArn) throw new Error("queue missing from mapping");
    if (!Number.isFinite(priority)) throw new Error("priority missing from mapping");
    const chk = this.b.id("check-agents");
    const pri = this.b.id("set-priority");
    const xfer = this.b.id("transfer");
    const entry = this.b.add("UpdateContactTargetQueue", { QueueId: queueArn }, { NextAction: chk, Errors: ERR(["NoMatchingError"], onFail) }, id);
    this.b.add(
      "CheckMetricData",
      { MetricType: metric },
      { NextAction: onFail, Conditions: [{ NextAction: pri, Condition: { Operator: "NumberGreaterThan", Operands: ["0"] } }], Errors: ERR(["NoMatchingError"], onFail) },
      chk,
    );
    this.b.add("UpdateContactRoutingBehavior", { QueuePriority: String(priority) }, { NextAction: xfer, Errors: ERR(["NoMatchingError"], xfer) }, pri);
    this.b.add("TransferContactToQueue", {}, { Errors: [...ERR(["QueueAtCapacity"], onFail), ...ERR(["NoMatchingError"], onFail)] }, xfer);
    return entry;
  }

  /** Agents check only (Avaya "goto ... if available-agents in skill S > 0"). */
  agentsCheck(queueArn: string, metric: "NumberOfAgentsStaffed" | "NumberOfAgentsAvailable", onTrue: string, onFalse: string, id?: string): string {
    const chk = this.b.id("check-agents");
    const entry = this.b.add("UpdateContactTargetQueue", { QueueId: queueArn }, { NextAction: chk, Errors: ERR(["NoMatchingError"], onFalse) }, id);
    this.b.add(
      "CheckMetricData",
      { MetricType: metric },
      { NextAction: onFalse, Conditions: [{ NextAction: onTrue, Condition: { Operator: "NumberGreaterThan", Operands: ["0"] } }], Errors: ERR(["NoMatchingError"], onFalse) },
      chk,
    );
    return entry;
  }

  transferToFlow(flowArn: string, onFail: string, id?: string): string {
    if (!flowArn) throw new Error("flow missing from mapping");
    // connect-kit's lint wants a NextAction here as well; the transfer itself ends this flow.
    return this.b.add("TransferToFlow", { ContactFlowId: flowArn }, { NextAction: onFail, Errors: ERR(["NoMatchingError"], onFail) }, id);
  }

  start(firstAttrs: Record<string, string>, next: string, name: string) {
    // initialise variables the legacy script compares; if that fails, there is no safe path
    const init = Object.keys(firstAttrs).length
      ? this.b.add("UpdateContactAttributes", { Attributes: firstAttrs, TargetContact: "Current" }, { NextAction: next, Errors: ERR(["NoMatchingError"], this.disconnect) })
      : next;
    const start = this.b.add("UpdateFlowLoggingBehavior", { FlowLoggingBehavior: "Enabled" }, { NextAction: init });
    return this.b.build(start, name);
  }
}

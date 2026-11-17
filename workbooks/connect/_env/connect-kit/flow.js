"use strict";
/**
 * Amazon Connect flow language (Version 2019-10-30) stand-in: a structural validator,
 * a graph walker and a small interpreter that simulates a contact through a flow.
 *
 * It models the subset of actions the workbook uses. It is NOT the Connect runtime: it
 * exists so exercises can be graded offline. Semantics follow the published flow language
 * reference (Transitions.NextAction / Conditions / Errors, string parameters, JSONPath-like
 * references such as $.Attributes.x, $.External.x, $.Lex.IntentName).
 */

const CONNECT_SYNC_LAMBDA_MAX_SECONDS = 8;

/** Actions that end flow execution for the contact (no NextAction required). */
const TERMINAL = new Set([
  "DisconnectParticipant",
  "EndFlowModuleExecution",
  "TransferContactToQueue", // terminal on success; errors must still be handled
  "EndFlowExecution",
  "TransferToFlow",
]);

/**
 * Error types each action must handle. Mostly the flow language reference's own requirements; the
 * workbook is stricter in one place: GetParticipantInput must also route InputTimeLimitExceeded
 * (a silent caller must not fall through to a generic error path).
 */
const REQUIRED_ERRORS = {
  MessageParticipant: ["NoMatchingError"],
  InvokeLambdaFunction: ["NoMatchingError"],
  GetParticipantInput: ["InputTimeLimitExceeded", "NoMatchingCondition", "NoMatchingError"],
  ConnectParticipantWithLexBot: ["NoMatchingCondition", "NoMatchingError"],
  TransferContactToQueue: ["QueueAtCapacity", "NoMatchingError"],
  CheckHoursOfOperation: ["NoMatchingError"],
  CheckMetricData: ["NoMatchingError"],
  Compare: ["NoMatchingCondition"],
  UpdateContactTargetQueue: ["NoMatchingError"],
  UpdateContactAttributes: ["NoMatchingError"],
  InvokeFlowModule: ["NoMatchingError"],
  TransferToFlow: ["NoMatchingError"],
  UpdateContactRoutingBehavior: ["NoMatchingError"],
  UpdateRoutingCriteria: ["NoMatchingError"],
};

const KNOWN_TYPES = new Set([
  "MessageParticipant",
  "GetParticipantInput",
  "ConnectParticipantWithLexBot",
  "InvokeLambdaFunction",
  "UpdateContactAttributes",
  "UpdateContactTargetQueue",
  "UpdateContactRoutingBehavior",
  "UpdateContactRecordingBehavior",
  "UpdateContactRecordingAndAnalyticsBehavior",
  "UpdateRoutingCriteria",
  "UpdateContactData",
  "GetMetricData",
  "CreateTask",
  "TagContact",
  "EndFlowModuleExecution",
  "UpdateFlowLoggingBehavior",
  "UpdateContactEventHooks",
  "UpdateContactTextToSpeechVoice",
  "CheckHoursOfOperation",
  "CheckMetricData",
  "Compare",
  "Loop",
  "InvokeFlowModule",
  "TransferContactToQueue",
  "TransferToFlow",
  "DisconnectParticipant",
  "EndFlowExecution",
]);

function actionsById(flow) {
  const map = new Map();
  for (const a of flow.Actions || []) map.set(a.Identifier, a);
  return map;
}

/** Every outgoing edge of an action: {to, kind, label}. */
function edges(action) {
  const t = action.Transitions || {};
  const out = [];
  if (t.NextAction) out.push({ to: t.NextAction, kind: "next", label: "NextAction" });
  for (const c of t.Conditions || []) {
    const ops = (c.Condition && c.Condition.Operands) || [];
    out.push({ to: c.NextAction, kind: "condition", label: `${(c.Condition || {}).Operator || "?"}:${ops.join("|")}` });
  }
  for (const e of t.Errors || []) out.push({ to: e.NextAction, kind: "error", label: e.ErrorType });
  return out;
}

function errorTypes(action) {
  return new Set(((action.Transitions || {}).Errors || []).map((e) => e.ErrorType));
}

/** Collect every $.Attributes.<name> / $.External.<name> reference in an action's Parameters. */
function references(value, out = []) {
  if (typeof value === "string") {
    const re = /\$\.(Attributes|External|Lex\.SessionAttributes|Lex\.Slots)\.([A-Za-z0-9_\-]+)/g;
    let m;
    while ((m = re.exec(value)) !== null) out.push({ ns: m[1], name: m[2] });
  } else if (Array.isArray(value)) {
    value.forEach((v) => references(v, out));
  } else if (value && typeof value === "object") {
    Object.values(value).forEach((v) => references(v, out));
  }
  return out;
}

/** Tarjan SCC over the action graph. */
function stronglyConnected(flow) {
  const byId = actionsById(flow);
  let index = 0;
  const idx = new Map();
  const low = new Map();
  const onStack = new Set();
  const stack = [];
  const sccs = [];
  function visit(v) {
    idx.set(v, index);
    low.set(v, index);
    index++;
    stack.push(v);
    onStack.add(v);
    const a = byId.get(v);
    for (const e of a ? edges(a) : []) {
      if (!byId.has(e.to)) continue;
      if (!idx.has(e.to)) {
        visit(e.to);
        low.set(v, Math.min(low.get(v), low.get(e.to)));
      } else if (onStack.has(e.to)) {
        low.set(v, Math.min(low.get(v), idx.get(e.to)));
      }
    }
    if (low.get(v) === idx.get(v)) {
      const comp = [];
      let w;
      do {
        w = stack.pop();
        onStack.delete(w);
        comp.push(w);
      } while (w !== v);
      sccs.push(comp);
    }
  }
  for (const id of byId.keys()) if (!idx.has(id)) visit(id);
  return sccs;
}

function reachable(flow) {
  const byId = actionsById(flow);
  const seen = new Set();
  const todo = [flow.StartAction];
  while (todo.length) {
    const id = todo.pop();
    if (seen.has(id) || !byId.has(id)) continue;
    seen.add(id);
    for (const e of edges(byId.get(id))) todo.push(e.to);
  }
  return seen;
}

/**
 * Must-set analysis: for each action, the set of contact attribute names that are set on
 * EVERY path from StartAction to it. Lambda results ($.External) are tracked as a pseudo
 * attribute "__external__" that is set by InvokeLambdaFunction on its success edge only.
 */
function mustSetAttributes(flow) {
  const byId = actionsById(flow);
  const ids = [...reachable(flow)];
  const ALL = null; // top element: "everything" (not yet computed)
  const inSets = new Map(ids.map((id) => [id, ALL]));
  inSets.set(flow.StartAction, new Set());
  function outFor(action, inSet, edge) {
    const out = new Set(inSet);
    if (action.Type === "UpdateContactAttributes" && edge.kind !== "error") {
      for (const k of Object.keys((action.Parameters || {}).Attributes || {})) out.add(k);
    }
    if (action.Type === "InvokeLambdaFunction" && edge.kind !== "error") out.add("__external__");
    if (action.Type === "InvokeLambdaFunction" && edge.kind === "error") out.delete("__external__");
    return out;
  }
  let changed = true;
  let guard = 0;
  while (changed && guard++ < 1000) {
    changed = false;
    for (const id of ids) {
      const a = byId.get(id);
      const cur = inSets.get(id);
      if (cur === ALL) continue;
      for (const e of edges(a)) {
        if (!byId.has(e.to)) continue;
        const o = outFor(a, cur, e);
        const prev = inSets.get(e.to);
        let next;
        if (prev === ALL) next = o;
        else next = new Set([...prev].filter((x) => o.has(x)));
        if (prev === ALL || next.size !== prev.size) {
          inSets.set(e.to, next);
          changed = true;
        }
      }
    }
  }
  return inSets;
}

/**
 * Validate a flow. Returns {ok, issues:[{code, severity, actionId, message}]}.
 * Severity "error" fails ok; "warning" does not.
 *
 * options.knownAttributes: attribute names guaranteed set before this flow runs
 *   (e.g. set by an upstream flow); they do not trigger ATTR_BEFORE_SET.
 * options.queueFlow: true when the flow runs with a working queue already set.
 */
function validateFlow(flow, options = {}) {
  const issues = [];
  const add = (code, severity, actionId, message) => issues.push({ code, severity, actionId, message });
  if (!flow || typeof flow !== "object") {
    add("STRUCTURE", "error", null, "flow is not a JSON object");
    return { ok: false, issues };
  }
  if (flow.Version !== "2019-10-30") add("STRUCTURE", "error", null, `Version must be "2019-10-30", got ${JSON.stringify(flow.Version)}`);
  if (!Array.isArray(flow.Actions) || flow.Actions.length === 0) {
    add("STRUCTURE", "error", null, "Actions must be a non-empty array");
    return { ok: false, issues };
  }
  if (flow.Actions.length > 250) add("STRUCTURE", "error", null, `a flow may hold at most 250 actions, got ${flow.Actions.length}`);
  const byId = new Map();
  for (const a of flow.Actions) {
    if (!a.Identifier) add("STRUCTURE", "error", null, "action without Identifier");
    else if (a.Identifier.length > 50 || /[%:()\\/=$,;\[\]{}]/.test(a.Identifier)) add("STRUCTURE", "error", a.Identifier, "Identifier must be <= 50 chars without % : ( ) \\ / = $ , ; [ ] { }");
    else if (byId.has(a.Identifier)) add("STRUCTURE", "error", a.Identifier, "duplicate Identifier");
    else byId.set(a.Identifier, a);
    if (!KNOWN_TYPES.has(a.Type)) add("UNKNOWN_TYPE", "error", a.Identifier, `unknown or unsupported action Type ${JSON.stringify(a.Type)}`);
    if (a.Parameters === undefined) add("STRUCTURE", "error", a.Identifier, "Parameters is required (use {} when empty)");
    if (a.Transitions === undefined) add("STRUCTURE", "error", a.Identifier, "Transitions is required (use {} when empty)");
  }
  if (!byId.has(flow.StartAction)) add("STRUCTURE", "error", null, `StartAction ${JSON.stringify(flow.StartAction)} is not an action`);

  for (const a of flow.Actions) {
    for (const e of edges(a)) {
      if (!byId.has(e.to)) add("BROKEN_TRANSITION", "error", a.Identifier, `${e.label} points at missing action ${JSON.stringify(e.to)}`);
    }
    const t = a.Transitions || {};
    const terminal = TERMINAL.has(a.Type);
    if (!terminal && !t.NextAction && a.Type !== "Loop" && !(t.Conditions || []).length) {
      add("DEAD_END", "error", a.Identifier, `${a.Type} has no NextAction: the contact would be dropped here`);
    }
    if (a.Type === "Loop") {
      const ops = (t.Conditions || []).map((c) => ((c.Condition || {}).Operands || [])[0]);
      if (!ops.includes("ContinueLooping") || !ops.includes("DoneLooping")) {
        add("DEAD_END", "error", a.Identifier, "Loop needs both ContinueLooping and DoneLooping conditions");
      }
      const n = Number((a.Parameters || {}).LoopCount);
      if (!Number.isInteger(n) || n < 1) add("STRUCTURE", "error", a.Identifier, "Loop.LoopCount must be a positive integer string");
    }
    if (a.Type === "CheckMetricData") {
      const metric = (a.Parameters || {}).MetricType || "";
      const conds = t.Conditions || [];
      if (/^NumberOfAgents/.test(metric) && conds.some((c) => !((c.Condition || {}).Operator === "NumberGreaterThan" && ((c.Condition || {}).Operands || [])[0] === "0"))) {
        add("STRUCTURE", "error", a.Identifier, `${metric} only supports the condition NumberGreaterThan 0`);
      }
      if (!t.NextAction && !errorTypes(a).has("NoMatchingCondition")) {
        add("DEAD_END", "error", a.Identifier, "CheckMetricData has no branch for the condition being false (NextAction)");
      }
    }
    if (a.Type === "CheckHoursOfOperation") {
      const ops = (t.Conditions || []).map((c) => ((c.Condition || {}).Operands || [])[0]).sort().join(",");
      if (ops !== "False,True") add("DEAD_END", "error", a.Identifier, "CheckHoursOfOperation needs exactly the conditions Equals True and Equals False");
    }
    const need = REQUIRED_ERRORS[a.Type] || [];
    const have = errorTypes(a);
    for (const err of need) {
      if (!have.has(err)) add("MISSING_ERROR_BRANCH", "error", a.Identifier, `${a.Type} does not handle ${err}`);
    }
    if (a.Type === "InvokeLambdaFunction") {
      const p = a.Parameters || {};
      if (!p.LambdaFunctionARN) add("STRUCTURE", "error", a.Identifier, "InvokeLambdaFunction needs LambdaFunctionARN");
      const secs = Number(p.InvocationTimeLimitSeconds);
      const mode = p.InvocationType || "SYNCHRONOUS";
      if (mode === "SYNCHRONOUS" && (!Number.isFinite(secs) || secs < 1 || secs > CONNECT_SYNC_LAMBDA_MAX_SECONDS)) {
        add("LAMBDA_TIMEOUT", "error", a.Identifier, `InvocationTimeLimitSeconds must be 1-${CONNECT_SYNC_LAMBDA_MAX_SECONDS} for a synchronous invoke, got ${JSON.stringify(p.InvocationTimeLimitSeconds)}`);
      }
    }
    if (a.Type === "GetParticipantInput") {
      const p = a.Parameters || {};
      if (!(p.Text || p.SSML || p.PromptId || p.Media)) add("STRUCTURE", "error", a.Identifier, "GetParticipantInput needs a prompt (Text, SSML, PromptId or Media)");
      if (p.StoreInput !== "True" && !(t.Conditions || []).length) add("STRUCTURE", "error", a.Identifier, "menu without conditions");
    }
  }

  // Unreachable actions (warning) and cycles without a bounding Loop (error).
  const reach = reachable(flow);
  for (const id of byId.keys()) if (!reach.has(id)) add("UNREACHABLE", "warning", id, "action is not reachable from StartAction");
  for (const comp of stronglyConnected(flow)) {
    const selfLoop = comp.length === 1 && edges(byId.get(comp[0]) || {}).some((e) => e.to === comp[0]);
    if (comp.length < 2 && !selfLoop) continue;
    if (!comp.some((id) => reach.has(id))) continue;
    const loops = comp.filter((id) => (byId.get(id) || {}).Type === "Loop");
    if (!loops.length) {
      add("UNBOUNDED_LOOP", "error", comp[0], `cycle through [${comp.join(", ")}] has no Loop block bounding it`);
    } else {
      const exits = loops.some((id) => edges(byId.get(id)).some((e) => e.label.endsWith("DoneLooping") && !comp.includes(e.to)));
      if (!exits) add("UNBOUNDED_LOOP", "error", loops[0], "Loop DoneLooping branch does not leave the cycle");
    }
  }

  // Attributes and Lambda results used before they are set on every path.
  const must = mustSetAttributes(flow);
  const known = new Set(options.knownAttributes || []);
  for (const id of reach) {
    const a = byId.get(id);
    const inSet = must.get(id);
    if (!inSet) continue;
    const refs = references(a.Parameters || {});
    // UpdateContactAttributes may reference a value it sets elsewhere in the same block; only the source matters.
    for (const r of refs) {
      if (r.ns === "Attributes" && !inSet.has(r.name) && !known.has(r.name)) {
        add("ATTR_BEFORE_SET", "error", id, `$.Attributes.${r.name} is used before it is set on every path`);
      }
      if (r.ns === "External" && !inSet.has("__external__")) {
        add("ATTR_BEFORE_SET", "error", id, `$.External.${r.name} is used where no successful Lambda invoke precedes it on every path`);
      }
    }
  }

  // Transfer to queue needs a working queue on every path (unless the flow runs in a queue context).
  if (!options.queueFlow) {
    const queueSet = new Map();
    const order = [...reach];
    const ALL = null;
    order.forEach((id) => queueSet.set(id, ALL));
    queueSet.set(flow.StartAction, false);
    let changed = true;
    let guard = 0;
    while (changed && guard++ < 1000) {
      changed = false;
      for (const id of order) {
        const a = byId.get(id);
        const cur = queueSet.get(id);
        if (cur === ALL) continue;
        for (const e of edges(a)) {
          if (!byId.has(e.to)) continue;
          const o = cur || (a.Type === "UpdateContactTargetQueue" && e.kind !== "error");
          const prev = queueSet.get(e.to);
          const next = prev === ALL ? o : prev && o;
          if (prev !== next) {
            queueSet.set(e.to, next);
            changed = true;
          }
        }
      }
    }
    for (const id of reach) {
      if (byId.get(id).Type === "TransferContactToQueue" && queueSet.get(id) !== true) {
        add("TRANSFER_WITHOUT_QUEUE", "error", id, "TransferContactToQueue is reachable on a path with no Set working queue (UpdateContactTargetQueue)");
      }
    }
  }

  return { ok: !issues.some((i) => i.severity === "error"), issues };
}

/* ------------------------------------------------------------------ interpreter */

function resolveRef(value, ctx) {
  if (typeof value !== "string") return value;
  return value.replace(/\$\.([A-Za-z]+(?:\.[A-Za-z0-9_\-]+)*)/g, (whole, path) => {
    const parts = path.split(".");
    let cur;
    switch (parts[0]) {
      case "Attributes": cur = ctx.attributes; break;
      case "External": cur = ctx.external; break;
      case "Lex": cur = ctx.lex; break;
      case "StoredCustomerInput": return ctx.storedInput == null ? "" : String(ctx.storedInput);
      case "CustomerEndpoint": cur = { Address: ctx.customerEndpoint }; break;
      case "Channel": return ctx.channel;
      case "ContactId": return ctx.contactId;
      default: return whole;
    }
    for (const p of parts.slice(1)) cur = cur == null ? undefined : cur[p];
    return cur == null ? "" : String(cur);
  });
}

function compare(operator, left, operands) {
  const l = left;
  const r = operands[0];
  switch (operator) {
    case "Equals": return String(l) === String(r);
    case "TextContains": return String(l).includes(String(r));
    case "TextStartsWith": return String(l).startsWith(String(r));
    case "TextEndsWith": return String(l).endsWith(String(r));
    case "NumberGreaterThan": return Number(l) > Number(r);
    case "NumberGreaterOrEqualTo": return Number(l) >= Number(r);
    case "NumberLessThan": return Number(l) < Number(r);
    case "NumberLessOrEqualTo": return Number(l) <= Number(r);
    default: throw new Error(`interpreter: unsupported Condition.Operator ${operator}`);
  }
}

/**
 * Simulate one contact through a flow.
 *
 * scenario = {
 *   channel: "VOICE" | "CHAT", customerEndpoint: "+15555550100", contactId,
 *   attributes: {...}              initial contact attributes
 *   inputs: ["1", null, ...]       caller responses for GetParticipantInput in order; null = timeout
 *   lambdas: { [arnOrSuffix]: (payload) => ({...}) | {__error: "timeout"|"error"} | number(ms) },
 *   lambdaLatencyMs: { [arnOrSuffix]: ms }  simulated duration; > time limit -> error branch
 *   hours: { [hoursIdOrSuffix]: true|false },
 *   metrics: { [queueIdOrSuffix]: { NumberOfAgentsAvailable: n, NumberOfAgentsStaffed: n, NumberOfAgentsOnline: n, ContactsInQueue: n } },
 *   queueAtCapacity: { [queueIdOrSuffix]: true },
 *   lex: [{ intent: "ResetPassword", slots: {...}, sessionAttributes: {...} } | {error: "timeout"}],
 *   modules: { [moduleId]: flowJson },
 *   maxSteps: 300
 * }
 * returns { outcome, queue, attributes, trace, prompts, lambdaCalls, steps }
 * outcome: "Disconnected" | "TransferredToQueue" | "Ended" | "TransferredToFlow" | "DeadEnd" | "StepLimit" | "Error"
 */
function simulate(flow, scenario = {}) {
  const byId = actionsById(flow);
  const ctx = {
    attributes: { ...(scenario.attributes || {}) },
    external: {},
    lex: {},
    storedInput: null,
    customerEndpoint: scenario.customerEndpoint || "+15555550100",
    channel: scenario.channel || "VOICE",
    contactId: scenario.contactId || "00000000-0000-4000-8000-000000000001",
    queue: scenario.queue || null,
    routing: {},
  };
  const inputs = [...(scenario.inputs || [])];
  const lexTurns = [...(scenario.lex || [])];
  const loopCounters = new Map();
  const trace = [];
  const prompts = [];
  const lambdaCalls = [];
  const maxSteps = scenario.maxSteps || 300;
  const pick = (table, key) => {
    if (!table || key == null) return undefined;
    if (key in table) return table[key];
    const hit = Object.keys(table).find((k) => String(key).endsWith(k));
    return hit === undefined ? undefined : table[hit];
  };

  let current = flow.StartAction;
  let steps = 0;
  const finish = (outcome, extra = {}) => ({
    outcome,
    queue: ctx.queue,
    attributes: ctx.attributes,
    external: ctx.external,
    routing: ctx.routing,
    trace,
    prompts,
    lambdaCalls,
    steps,
    ...extra,
  });

  while (true) {
    if (steps++ >= maxSteps) return finish("StepLimit");
    const a = byId.get(current);
    if (!a) return finish("Error", { error: `missing action ${current}` });
    const t = a.Transitions || {};
    const p = a.Parameters || {};
    const errorTo = (type) => {
      const e = (t.Errors || []).find((x) => x.ErrorType === type);
      return e ? e.NextAction : null;
    };
    let next = null;
    let branch = "NextAction";
    const go = (to, label) => { next = to; branch = label; };
    const fail = (type) => {
      const to = errorTo(type);
      if (!to) return true;
      go(to, `Error:${type}`);
      return false;
    };

    switch (a.Type) {
      case "MessageParticipant":
        prompts.push(resolveRef(p.Text || p.SSML || p.PromptId || "", ctx));
        go(t.NextAction, "NextAction");
        break;
      case "UpdateFlowLoggingBehavior":
      case "UpdateContactRecordingBehavior":
      case "UpdateContactRecordingAndAnalyticsBehavior":
      case "UpdateContactData":
      case "TagContact":
      case "GetMetricData":
      case "CreateTask":
      case "UpdateContactEventHooks":
      case "UpdateContactTextToSpeechVoice":
        go(t.NextAction, "NextAction");
        break;
      case "UpdateContactAttributes": {
        for (const [k, v] of Object.entries(p.Attributes || {})) ctx.attributes[k] = resolveRef(v, ctx);
        go(t.NextAction, "NextAction");
        break;
      }
      case "UpdateContactTargetQueue":
        ctx.queue = resolveRef(p.QueueId, ctx);
        go(t.NextAction, "NextAction");
        break;
      case "UpdateContactRoutingBehavior":
        if (p.QueuePriority !== undefined) ctx.routing.priority = Number(resolveRef(p.QueuePriority, ctx));
        if (p.QueueTimeAdjustmentSeconds !== undefined) ctx.routing.timeAdjustment = Number(resolveRef(p.QueueTimeAdjustmentSeconds, ctx));
        go(t.NextAction, "NextAction");
        break;
      case "UpdateRoutingCriteria":
        ctx.routing.criteria = p.RoutingCriteria;
        go(t.NextAction, "NextAction");
        break;
      case "GetParticipantInput": {
        prompts.push(resolveRef(p.Text || p.SSML || p.PromptId || "", ctx));
        const input = inputs.length ? inputs.shift() : null;
        if (input === null || input === undefined) {
          if (fail("InputTimeLimitExceeded")) return finish("DeadEnd", { at: a.Identifier, reason: "InputTimeLimitExceeded unhandled" });
          break;
        }
        if (p.StoreInput === "True") {
          ctx.storedInput = input;
          go(t.NextAction, "NextAction");
          break;
        }
        const hit = (t.Conditions || []).find((c) => compare(c.Condition.Operator, input, c.Condition.Operands));
        if (hit) go(hit.NextAction, `Condition:${input}`);
        else if (fail("NoMatchingCondition")) return finish("DeadEnd", { at: a.Identifier, reason: "NoMatchingCondition unhandled" });
        break;
      }
      case "ConnectParticipantWithLexBot": {
        prompts.push(resolveRef(p.Text || "", ctx));
        const turn = lexTurns.length ? lexTurns.shift() : { error: "timeout" };
        if (turn.error) {
          const type = turn.error === "timeout" ? "InputTimeLimitExceeded" : "NoMatchingError";
          if (fail(type) && fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: `${type} unhandled` });
          break;
        }
        ctx.lex = { IntentName: turn.intent, Slots: turn.slots || {}, SessionAttributes: turn.sessionAttributes || {} };
        const hit = (t.Conditions || []).find((c) => compare(c.Condition.Operator, turn.intent, c.Condition.Operands));
        if (hit) go(hit.NextAction, `Intent:${turn.intent}`);
        else if (fail("NoMatchingCondition")) return finish("DeadEnd", { at: a.Identifier, reason: "NoMatchingCondition unhandled" });
        break;
      }
      case "InvokeLambdaFunction": {
        const arn = p.LambdaFunctionARN;
        const limitMs = Number(p.InvocationTimeLimitSeconds || CONNECT_SYNC_LAMBDA_MAX_SECONDS) * 1000;
        const fn = pick(scenario.lambdas, arn);
        const latency = pick(scenario.lambdaLatencyMs, arn) || 0;
        const payload = { Details: { ContactData: { Attributes: { ...ctx.attributes }, Channel: ctx.channel, ContactId: ctx.contactId, CustomerEndpoint: { Address: ctx.customerEndpoint, Type: "TELEPHONE_NUMBER" } }, Parameters: Object.fromEntries(Object.entries(p.LambdaInvocationAttributes || {}).map(([k, v]) => [k, resolveRef(v, ctx)])) }, Name: "ContactFlowEvent" };
        lambdaCalls.push({ arn, payload, latencyMs: latency });
        let result;
        try {
          result = fn ? fn(payload) : { __error: "not-configured" };
        } catch (err) {
          result = { __error: String(err && err.message) };
        }
        const flat = result && !result.__error && Object.values(result).every((v) => ["string", "number", "boolean"].includes(typeof v));
        if (latency > limitMs || !result || result.__error || ((p.ResponseValidation || {}).ResponseType !== "JSON" && !flat)) {
          ctx.external = {};
          if (fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: "Lambda error unhandled" });
          break;
        }
        ctx.external = Object.fromEntries(Object.entries(result).map(([k, v]) => [k, typeof v === "object" ? v : String(v)]));
        go(t.NextAction, "NextAction");
        break;
      }
      case "Compare": {
        const left = resolveRef(p.ComparisonValue, ctx);
        const hit = (t.Conditions || []).find((c) => compare(c.Condition.Operator, left, c.Condition.Operands));
        if (hit) go(hit.NextAction, `Condition:${left}`);
        else if (fail("NoMatchingCondition")) return finish("DeadEnd", { at: a.Identifier, reason: "NoMatchingCondition unhandled" });
        break;
      }
      case "CheckHoursOfOperation": {
        const id = p.HoursOfOperationId || ctx.queue;
        const open = pick(scenario.hours, id);
        if (open === undefined) {
          if (fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: "hours unknown" });
          break;
        }
        const label = open ? "True" : "False";
        const hit = (t.Conditions || []).find((c) => compare(c.Condition.Operator, label, c.Condition.Operands));
        if (hit) go(hit.NextAction, `Condition:${label}`);
        else if (fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: "hours branch missing" });
        break;
      }
      case "CheckMetricData": {
        const q = p.QueueId ? resolveRef(p.QueueId, ctx) : ctx.queue;
        const m = pick(scenario.metrics, q);
        const metric = p.MetricType;
        if (!q || !m || m[metric] === undefined) {
          if (fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: `no metric ${metric} for queue ${q}` });
          break;
        }
        const hit = (t.Conditions || []).find((c) => compare(c.Condition.Operator, m[metric], c.Condition.Operands));
        if (hit) go(hit.NextAction, `Condition:${metric}=${m[metric]}`);
        else if (t.NextAction) go(t.NextAction, `False:${metric}=${m[metric]}`);
        else if (fail("NoMatchingCondition")) return finish("DeadEnd", { at: a.Identifier, reason: "NoMatchingCondition unhandled" });
        break;
      }
      case "Loop": {
        const n = Number(p.LoopCount);
        const used = loopCounters.get(a.Identifier) || 0;
        const label = used < n ? "ContinueLooping" : "DoneLooping";
        loopCounters.set(a.Identifier, used < n ? used + 1 : 0);
        const hit = (t.Conditions || []).find((c) => (c.Condition.Operands || [])[0] === label);
        if (!hit) return finish("DeadEnd", { at: a.Identifier, reason: `Loop ${label} missing` });
        go(hit.NextAction, label);
        break;
      }
      case "InvokeFlowModule": {
        const mod = pick(scenario.modules, p.FlowModuleId);
        if (!mod) {
          if (fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: "module missing" });
          break;
        }
        const sub = simulate(mod, { ...scenario, attributes: ctx.attributes, inputs, lex: lexTurns, maxSteps: maxSteps - steps });
        trace.push(...sub.trace.map((x) => ({ ...x, module: p.FlowModuleId })));
        prompts.push(...sub.prompts);
        Object.assign(ctx.attributes, sub.attributes);
        if (sub.outcome !== "Ended") return finish(sub.outcome, { at: sub.at, reason: sub.reason });
        go(t.NextAction, "NextAction");
        break;
      }
      case "TransferContactToQueue": {
        if (!ctx.queue) {
          if (fail("NoMatchingError")) return finish("DeadEnd", { at: a.Identifier, reason: "no working queue" });
          break;
        }
        if (pick(scenario.queueAtCapacity, ctx.queue)) {
          if (fail("QueueAtCapacity")) return finish("DeadEnd", { at: a.Identifier, reason: "QueueAtCapacity unhandled" });
          break;
        }
        trace.push({ id: a.Identifier, type: a.Type, branch: "Transferred" });
        return finish("TransferredToQueue");
      }
      case "TransferToFlow":
        trace.push({ id: a.Identifier, type: a.Type, branch: "Transferred" });
        return finish("TransferredToFlow", { flowId: p.ContactFlowId });
      case "DisconnectParticipant":
        trace.push({ id: a.Identifier, type: a.Type, branch: "Disconnect" });
        return finish("Disconnected");
      case "EndFlowExecution":
      case "EndFlowModuleExecution":
        trace.push({ id: a.Identifier, type: a.Type, branch: "End" });
        return finish("Ended");
      default:
        return finish("Error", { error: `interpreter does not model ${a.Type}` });
    }
    trace.push({ id: a.Identifier, type: a.Type, branch });
    if (!next) return finish("DeadEnd", { at: a.Identifier, reason: `${a.Type} has no next action` });
    current = next;
  }
}

/** Every simple path summary is too large; instead enumerate terminal outcomes by DFS over branches. */
function terminalsReachable(flow) {
  const byId = actionsById(flow);
  const out = new Set();
  for (const id of reachable(flow)) {
    const a = byId.get(id);
    if (TERMINAL.has(a.Type)) out.add(a.Type);
  }
  return out;
}

module.exports = {
  CONNECT_SYNC_LAMBDA_MAX_SECONDS,
  REQUIRED_ERRORS,
  KNOWN_TYPES,
  validateFlow,
  simulate,
  edges,
  reachable,
  stronglyConnected,
  terminalsReachable,
  resolveRef,
};

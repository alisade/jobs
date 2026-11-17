"""Generate incident evidence for aiarch/w5-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""OPS-5520  P3  Change assistant traces are broken in Transaction Search
Opened 2026-11-13 14:10 by AgentOps (K. Iyer)

Since the change assistant started calling tools in parallel (2.6.0, "parallel tool calls"),
the trace view in CloudWatch shows the agent span and the model call, but the tool spans and
the tool server spans appear as separate traces with no parent. The latency dashboard per
conversation is wrong because tool time is missing. Turns that call a single tool look fine.

On-call notes:
- 14:25 (K. Iyer) The tool server runs ADOT with OTEL_PROPAGATORS=tracecontext,baggage,xray and
  the agent with tracecontext,baggage. Mismatch? Proposing to align both on xray.
- 14:31 X-Ray sampling rule for the tool server is 5%; maybe the parent was sampled out.
""")
spans = [
 {"traceId": "6a1f0c2e9b7d4e51a3c08f2d7b9e6c41", "spanId": "a1b2c3d4e5f60718", "parentSpanId": None, "name": "invoke_agent change_assistant", "kind": "INTERNAL"},
 {"traceId": "6a1f0c2e9b7d4e51a3c08f2d7b9e6c41", "spanId": "b1b2c3d4e5f60719", "parentSpanId": "a1b2c3d4e5f60718", "name": "chat us.anthropic.claude-haiku-4-5-20251001-v1:0", "kind": "INTERNAL"},
 {"traceId": "0f9e8d7c6b5a49382716a5b4c3d2e1f0", "spanId": "c1b2c3d4e5f6071a", "parentSpanId": None, "name": "execute_tool get_change", "kind": "CLIENT", "thread": "tool_0"},
 {"traceId": "0f9e8d7c6b5a49382716a5b4c3d2e1f0", "spanId": "d1b2c3d4e5f6071b", "parentSpanId": "c1b2c3d4e5f6071a", "name": "tools/call get_change", "kind": "SERVER"},
 {"traceId": "77aa66bb55cc44dd33ee22ff11009988", "spanId": "e1b2c3d4e5f6071c", "parentSpanId": None, "name": "execute_tool get_change", "kind": "CLIENT", "thread": "tool_1"},
 {"traceId": "77aa66bb55cc44dd33ee22ff11009988", "spanId": "f1b2c3d4e5f6071d", "parentSpanId": "e1b2c3d4e5f6071c", "name": "tools/call get_change", "kind": "SERVER"},
]
(out / "exported-spans-turn-parallel.json").write_text(json.dumps(spans, indent=1) + "\n")
single = [
 {"traceId": "5c5c5c5c5c5c4c4c3c3c2c2c1c1c0c0c", "spanId": "1111111111111111", "parentSpanId": None, "name": "invoke_agent change_assistant", "kind": "INTERNAL"},
 {"traceId": "5c5c5c5c5c5c4c4c3c3c2c2c1c1c0c0c", "spanId": "2222222222222222", "parentSpanId": "1111111111111111", "name": "execute_tool get_change", "kind": "CLIENT", "thread": "MainThread"},
 {"traceId": "5c5c5c5c5c5c4c4c3c3c2c2c1c1c0c0c", "spanId": "3333333333333333", "parentSpanId": "2222222222222222", "name": "tools/call get_change", "kind": "SERVER"},
]
(out / "exported-spans-turn-single.json").write_text(json.dumps(single, indent=1) + "\n")
(out / "otel-env.txt").write_text("""# agent (AgentCore Runtime, ADOT auto-instrumentation)
OTEL_PROPAGATORS=tracecontext,baggage
OTEL_TRACES_SAMPLER=parentbased_always_on
# tool server (behind Gateway)
OTEL_PROPAGATORS=tracecontext,baggage,xray
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.05
""")

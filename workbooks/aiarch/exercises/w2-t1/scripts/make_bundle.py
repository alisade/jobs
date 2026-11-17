"""Generate incident evidence for aiarch/w2-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""INC-20433  P1 (security)  Access-review assistant showed another team's reviews
Opened 2026-11-12 10:52 by M. Chen (claims manager)

"I asked what was pending for my team and it answered about lwong and ledger-admin. That is a
payments entitlement, not mine." Two more reports by 11:30. Release 2.3.0 went out 2026-11-10.

Also from FinOps: Bedrock input tokens for the access-review agent climb all day and reset
every night at 02:00, which is when the Runtime sessions recycle after the overnight deploy.

On-call notes:
- 11:05 (R. Patel) 2.3.0 raised temperature from 0.2 to 0.7 (CHG-8790). Higher temperature
  makes the model hallucinate names. Proposing a rollback of the config.
- 11:20 (R. Patel) System prompt says "never reveal other teams"; maybe make it stronger.
""")
lines = []
tok = 1180
users = [("sess-7f1a", "lwong", "payments"), ("sess-91c2", "mchen", "claims"), ("sess-0b77", "aokafor", "underwriting"),
         ("sess-7f1a", "lwong", "payments"), ("sess-c3d9", "tkhan", "payments"), ("sess-91c2", "mchen", "claims")]
for i, (sid, user, team) in enumerate(users * 3):
    tok += 410 + (i % 3) * 25
    lines.append(json.dumps({"ts": f"2026-11-12T{9 + i // 6:02d}:{(i * 7) % 60:02d}:11Z", "level": "INFO",
                             "msg": "turn complete", "runtimeSessionId": sid, "user": user, "team": team,
                             "agent": "access_reviews", "pid": 7, "agent_object_id": "0x7f3e2c1a9d50",
                             "gen_ai.usage.input_tokens": tok, "gen_ai.usage.output_tokens": 96,
                             "messages_in_context": 2 + 4 * (i + 1)}))
(out / "app-logs.jsonl").write_text("\n".join(lines) + "\n")
(out / "transcript-sess-91c2.txt").write_text("""runtimeSessionId sess-91c2  user mchen  team claims
[mchen] what is pending for my team?
assistant: You have two pending reviews: lwong needs ledger-admin and jdiaz needs prod-db-read.
           There is also AR-903 for mchen (claims-export).
""")
(out / "release-2.3.0-notes.md").write_text("""# 2.3.0 (2026-11-10)
- Temperature 0.2 -> 0.7 (CHG-8790).
- Performance: reuse the specialist Agent instead of building one per request (saves ~40 ms per turn).
- Log agent_object_id and messages_in_context per turn.
""")

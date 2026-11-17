"""Generate incident evidence for aiarch/ai-t1 into incident/ (stdlib only)."""
import json
import sys
from pathlib import Path

out = Path(sys.argv[1] if len(sys.argv) > 1 else "incident")
out.mkdir(parents=True, exist_ok=True)
(out / "PAGE.txt").write_text("""FIN-2210  P3  Bedrock spend for the help desk agent up 3x since 2026-11-10
Opened 2026-11-14 09:00 by FinOps (J. Alvarez)

Daily Bedrock cost for the lighthouse-helpdesk application inference profile went from about
USD 41 to about USD 128 with flat traffic (about 9,000 turns a day). Release 3.1.0 of the help
desk agent shipped on 2026-11-10.

On-call notes:
- 09:20 (T. Ruiz) 3.1.0 trimmed the system prompt. If the prefix is now under the model's
  minimum cacheable size, caching silently stops. Proposing to pad the prompt.
- 09:31 (T. Ruiz) Or the 5-minute cache TTL is too short for our traffic; ask AWS for a longer
  TTL.
""")
before = [{"ts": f"2026-11-09T10:{m:02d}:00Z", "release": "3.0.4", "request_id": f"req-0091{m:02d}",
           "usage": {"inputTokens": 41, "outputTokens": 150, "cacheReadInputTokens": 2152 if m else 0,
                     "cacheWriteInputTokens": 0 if m else 2152}} for m in range(6)]
after = [{"ts": f"2026-11-12T10:{m:02d}:00Z", "release": "3.1.0", "request_id": f"req-1182{m:02d}",
          "usage": {"inputTokens": 8, "outputTokens": 150, "cacheReadInputTokens": 0, "cacheWriteInputTokens": 2180}}
         for m in range(6)]
(out / "converse-usage.jsonl").write_text("\n".join(json.dumps(x) for x in before + after) + "\n")
(out / "release-3.1.0-notes.md").write_text("""# 3.1.0 (2026-11-10)
- The model now sees the current time and the signed-in user (fixes "is my approval still valid").
- Support: request id added to the prompt so transcripts can be matched to logs.
- System prompt reworded (same length within 2%).
""")
(out / "daily-cost.txt").write_text("""date        turns  usd    cache_read_tokens  cache_write_tokens
2026-11-07  8890   40.2   19.0M              0.09M
2026-11-08  9120   41.3   19.5M              0.10M
2026-11-09  9015   40.8   19.3M              0.09M
2026-11-10  9230   117.9  4.1M               15.8M
2026-11-11  8960   127.6  0.0M               19.5M
2026-11-12  9105   128.9  0.0M               19.8M
""")

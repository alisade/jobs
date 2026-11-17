"""Replay a brownout locally against the deployed config: the risk API hangs, then a
customer adds to cart and checks out. Prints what the model would read and the decision
log. Usage: python scripts/replay_brownout.py [path/to/trust.env]"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from northwind_trust import RiskDecision, RiskRequest, build_backend, build_executor, read_env_file  # noqa: E402


class HangingRisk:
    """Halyard during the brownout: /v2/assess takes ~9 s."""

    async def assess(self, request: RiskRequest) -> RiskDecision:
        await asyncio.sleep(9)
        raise AssertionError("unreachable inside any sane budget")


async def main() -> None:
    env_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "deploy" / "trust.env"
    log = []
    backend = build_backend(read_env_file(env_path), HangingRisk(), decision_log=log.append)
    executor = build_executor(backend, session_id="replay-session", user_id="demo-user")
    await executor.execute("search_products", {"query": "yoga mat"})
    for name, args in (
        ("add_to_cart", {"product_id": "AR-1301", "quantity": 1}),
        ("checkout", {"note": "replay"}),
    ):
        out = await executor.execute(name, args)
        events = [e.type for e in out.events]
        print(f"{name:12s} is_error={out.is_error!s:5s} blocked={out.blocked!s:6s} events={events}")
        print(f"{'':12s} model reads: {out.result_text[:110]}")
    print("\ndecision log:")
    for record in log:
        print("  " + record.model_dump_json())


if __name__ == "__main__":
    asyncio.run(main())

"""Replay production-shaped traffic through assistant_gateway.gateway on a fake clock.

40 questions; after release 2026.11.10 about a third of answers are long product comparisons
(1,800-2,000 output tokens). Prints what the provider billed versus what users received.
Usage: simulate.py [--csv out.csv]   (--csv writes a usage export like finance's)
"""

import csv
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from assistant_gateway.clock import FakeClock  # noqa: E402
from assistant_gateway.gateway import Gateway, GatewayError  # noqa: E402
from assistant_gateway.pricing import cost_usd  # noqa: E402
from assistant_gateway.provider import FakeProvider, Reply  # noqa: E402

SYSTEM = "You are Kestrel Outfitters' shopping assistant. Compare products when asked. " * 30
QUESTIONS = [
    "Compare the Ridgeline 2P and the Basecamp 3P", "Is the Glacier 45qt cooler in stock in store 087?",
    "Best sleeping bag for 30F nights?", "Compare all your headlamps for trail running",
    "Where is my order KO-1182?", "Which pack fits a 19 inch torso?", "Compare the three camp chairs",
    "Do you price match?",
]


def main() -> None:
    rng = random.Random(11)
    clock = FakeClock()
    provider = FakeProvider(clock=clock)
    gw = Gateway(provider=provider, clock=clock)
    delivered = 0.0
    failed = 0
    for i in range(40):
        q = QUESTIONS[i % len(QUESTIONS)]
        long_answer = q.startswith("Compare")
        out = rng.randint(1800, 2000) if long_answer else rng.randint(90, 260)
        # a fresh script per question: the model gives the same length answer on every attempt
        provider.script = [Reply(output_tokens=out) for _ in range(12)]
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"{q} (conversation {i})"}]
        try:
            c = gw.answer(f"c-{i:03d}", msgs, max_tokens=2048)
            delivered += cost_usd(c.model, c.input_tokens, c.output_tokens)
        except GatewayError:
            failed += 1
    billed = sum(cost_usd(u["model"], u["input_tokens"], u["output_tokens"]) for u in provider.usage)
    print(f"questions: 40  answered: {40 - failed}  failed: {failed}")
    print(f"provider calls: {len(provider.calls)}  billed generations: {len(provider.usage)}")
    print(f"cost of answers users received: ${delivered:.2f}")
    print(f"cost billed by the provider:     ${billed:.2f}  ({billed / max(delivered, 1e-9):.1f}x)")
    if "--csv" in sys.argv:
        path = sys.argv[sys.argv.index("--csv") + 1]
        with open(path, "w", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["timestamp_offset_s", "model", "request_fingerprint", "input_tokens", "output_tokens", "duration_s", "billed_usd"])
            for u in provider.usage:
                w.writerow([f"{u['at']:.1f}", u["model"], u["fingerprint"], u["input_tokens"], u["output_tokens"],
                            u["duration_s"], f"{cost_usd(u['model'], u['input_tokens'], u['output_tokens']):.5f}"])


if __name__ == "__main__":
    main()

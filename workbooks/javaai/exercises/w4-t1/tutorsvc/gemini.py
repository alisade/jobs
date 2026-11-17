"""Stand-in for the Gemini client the service uses (google-genai, synchronous client.models.generate_content).

The real call is a blocking HTTPS request: 1-6 s for a tutor answer, up to 45 s for a long worked
example. Here latency is a parameter so tests can run fast. Do not change this file.
"""

from __future__ import annotations

import time


class BlockingGemini:
    def __init__(self, latency_s: float = 2.0):
        self.latency_s = latency_s
        self.calls = 0

    def generate_content(self, prompt: str) -> str:
        self.calls += 1
        time.sleep(self.latency_s)  # network wait: the thread blocks, the CPU is idle
        return f"Let's think it through step by step. What do you already know about: {prompt[:60]}?"

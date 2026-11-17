"""Model client interface and the scripted fake used locally and in tests (complete; do not edit).

Production wraps the provider SDK behind the same `complete()` signature.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

IN_PRICE_PER_MTOK = 3.00   # USD per million input tokens
OUT_PRICE_PER_MTOK = 15.00  # USD per million output tokens


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int

    @property
    def cost_usd(self) -> float:
        return (self.input_tokens * IN_PRICE_PER_MTOK + self.output_tokens * OUT_PRICE_PER_MTOK) / 1_000_000


@dataclass
class ScriptedLLM:
    """Returns scripted answers per supplier SKU, in order.

    script: {supplier_sku: [answer text for call 1, answer for call 2, ...]}
    The SKU is found in the prompt (build_prompt puts `SUPPLIER_SKU: <sku>` on its own line).
    """

    script: dict[str, list[str]]
    tokens_per_call: int | None = None
    prompts: list[str] = field(default_factory=list)
    on_call: Callable[[str], None] | None = None

    @property
    def calls(self) -> int:
        return len(self.prompts)

    def complete(self, prompt: str) -> LLMResult:
        self.prompts.append(prompt)
        if self.on_call:
            self.on_call(prompt)
        sku = None
        for line in prompt.splitlines():
            if line.startswith("SUPPLIER_SKU: "):
                sku = line.split(": ", 1)[1].strip()
                break
        answers = self.script.get(sku or "", [])
        n = sum(1 for p in self.prompts if f"SUPPLIER_SKU: {sku}\n" in p + "\n")
        text = answers[min(n, len(answers)) - 1] if answers else "{}"
        if self.tokens_per_call is not None:
            return LLMResult(text, self.tokens_per_call, self.tokens_per_call // 4)
        return LLMResult(text, max(1, len(prompt) // 4), max(1, len(text) // 4))

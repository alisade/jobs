"""The model call, stubbed for this exercise (w1-c1 built the real Converse loop)."""

from __future__ import annotations


def answer(prompt: str, memories: list[str]) -> str:
    prefs = f" (remembered: {'; '.join(memories)})" if memories else ""
    return f"Here is what I found for: {prompt}{prefs}"

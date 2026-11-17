"""Price list in USD per million tokens (fictional numbers for this exercise; do not edit)."""

PRICES = {
    "primary": {"input": 3.00, "output": 15.00},
    "fallback": {"input": 0.80, "output": 4.00},
}


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICES[model]
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000

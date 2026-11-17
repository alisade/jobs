"""Per-request cost for the finance dashboard. Reference solution.

Usage fields from the provider (all token counts):
  input_tokens                  uncached input after the last cache breakpoint
  cache_creation_input_tokens   prefix tokens written to the cache on this request
  cache_read_input_tokens       prefix tokens read from the cache on this request
  output_tokens                 generated tokens

Prices in USD per million tokens (see README). Cache writes cost 1.25x base input and cache reads
0.1x base input.
"""

PRICES = {"input": 3.00, "cache_write": 3.75, "cache_read": 0.30, "output": 15.00}


def cost_usd(usage: dict, prices: dict = PRICES) -> float:
    return (
        usage.get("input_tokens", 0) * prices["input"]
        + usage.get("cache_creation_input_tokens", 0) * prices["cache_write"]
        + usage.get("cache_read_input_tokens", 0) * prices["cache_read"]
        + usage.get("output_tokens", 0) * prices["output"]
    ) / 1_000_000


def cache_hit_ratio(usages: list[dict]) -> float:
    """Share of cacheable prefix tokens that were read from the cache."""
    read = sum(u.get("cache_read_input_tokens", 0) for u in usages)
    written = sum(u.get("cache_creation_input_tokens", 0) for u in usages)
    return read / (read + written) if read + written else 0.0

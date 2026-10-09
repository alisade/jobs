"""Week-1 slice: a hand-written agent loop over the blueprint's ShoppingToolExecutor."""

from .fake_client import FakeAnthropic, FakeBadRequest, load_script
from .loop import TurnResult, build_request, run_turn

__all__ = ["FakeAnthropic", "FakeBadRequest", "TurnResult", "build_request", "load_script", "run_turn"]

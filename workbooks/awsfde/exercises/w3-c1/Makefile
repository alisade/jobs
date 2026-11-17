# awsfde/w3-c1 -- retrieval eval harness and tenant-filtered Retrieve. Shared venv awsfde/.venv.
SHELL := /bin/bash
TRACK := $(abspath ../..)

.PHONY: setup test eval clean

setup:
	@bash "${TRACK}/_env/ensure-venv.sh"
	@echo "w3-c1 ready. Read README.md, then edit kb_eval/request.py and kb_eval/harness.py, then make eval."

eval:        ## evaluate both recorded KB configs into run/
	@"${TRACK}/.venv/bin/python" -m kb_eval.run

test:
	@bash "${TRACK}/_env/pytest.sh" tests

clean:
	@rm -rf .pytest_cache run
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@echo "w3-c1 clean (shared venv kept)"

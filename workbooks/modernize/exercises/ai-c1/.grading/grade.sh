#!/usr/bin/env bash
# Grade modernize/ai-c1: visible + hidden pytest scenarios with a scripted model (offline), in a temp copy.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 23 120

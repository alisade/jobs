#!/usr/bin/env bash
# Grade modernize/w6-t1: visible + hidden pytest checks on ci/pr_guard.py in a temp copy.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 24 120

#!/usr/bin/env bash
# Grade modernize/ai-t1: visible + hidden pytest checks of the request builder against the offline cache model.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 10 120

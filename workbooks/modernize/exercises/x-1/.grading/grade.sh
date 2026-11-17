#!/usr/bin/env bash
# Grade modernize/x-1: visible + hidden pytest checks of the Elytron CLI script (static dry run), in a temp copy.
# Last line: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 12 120

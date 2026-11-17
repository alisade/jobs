#!/usr/bin/env bash
# Grade backend/w1-t1: visible + hidden pytest tests in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track}/_env/grade-pytest.sh" "${ex_dir}" 15 240

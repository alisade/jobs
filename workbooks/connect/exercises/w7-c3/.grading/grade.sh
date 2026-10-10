#!/usr/bin/env bash
# Grade connect/w7-c3: visible + hidden pytest in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
connect_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${connect_dir}/_env/grade-pytest.sh" "${ex_dir}" 19 240

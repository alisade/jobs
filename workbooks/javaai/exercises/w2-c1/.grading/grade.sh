#!/usr/bin/env bash
# Grade javaai/w2-c1: visible + hidden jest tests in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-jest.sh" "${ex_dir}" 17 240

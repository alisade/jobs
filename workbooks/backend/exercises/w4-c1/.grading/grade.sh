#!/usr/bin/env bash
# Grade backend/w4-c1: visible + hidden jest tests in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track}/_env/grade-jest.sh" "${ex_dir}" 16 240

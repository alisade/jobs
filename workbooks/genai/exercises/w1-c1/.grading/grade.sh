#!/usr/bin/env bash
# Grade genai/w1-c1: visible + hidden jest tests in a temp copy (the learner's folder is not
# written to). Last line of stdout: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-jest.sh" "${ex_dir}" 27 240

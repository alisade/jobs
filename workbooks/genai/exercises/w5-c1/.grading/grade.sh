#!/usr/bin/env bash
# Grade genai/w5-c1 (design, review-only): completeness report, then GRADE_TESTS 0/0.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-design.sh" "${ex_dir}" DESIGN.md ANSWER.md

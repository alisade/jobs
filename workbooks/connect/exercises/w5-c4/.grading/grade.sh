#!/usr/bin/env bash
# Grade connect/w5-c4 (design, review-only): completeness report, then GRADE_TESTS 0/0.
# The rubric carries all 100 points; its automated row does not apply.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
connect_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${connect_dir}/_env/grade-design.sh" "${ex_dir}" DESIGN.md ANSWER.md

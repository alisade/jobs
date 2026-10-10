#!/usr/bin/env bash
# Grade connect/w2-c4: design exercise, review-only. Prints a completeness report and
# GRADE_TESTS {"passed": 0, "total": 0}; the rubric carries all 100 points.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
connect_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${connect_dir}/_env/grade-design.sh" "${ex_dir}" DESIGN.md ANSWER.md

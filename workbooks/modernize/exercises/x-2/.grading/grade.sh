#!/usr/bin/env bash
# Grade modernize/x-2: review-only design exercise. Prints a completeness report for the grader,
# then GRADE_TESTS {"passed": 0, "total": 0}; the rubric carries all 100 points.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-design.sh" "${ex_dir}" DESIGN.md ANSWER.md

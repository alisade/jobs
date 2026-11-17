#!/usr/bin/env bash
# Grade backend/x-1 (design, review-only): completeness report, then GRADE_TESTS 0/0.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track}/_env/grade-design.sh" "${ex_dir}" DESIGN.md ANSWER.md

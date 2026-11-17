#!/usr/bin/env bash
# Grade audit/x-2 (design, review-only): completeness report, then GRADE_TESTS 0/0.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
audit_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${audit_dir}/_env/grade-design.sh" "${ex_dir}" DESIGN.md ANSWER.md

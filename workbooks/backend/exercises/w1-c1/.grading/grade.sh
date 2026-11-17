#!/usr/bin/env bash
# Grade backend/w1-c1 (design, review-only): completeness report, then GRADE_TESTS 0/0.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track}/_env/grade-design.sh" "${ex_dir}" DESIGN.md adr/0001-tenancy-model.md adr/0002-service-integration.md ANSWER.md

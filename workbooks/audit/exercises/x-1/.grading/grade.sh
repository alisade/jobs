#!/usr/bin/env bash
# Grade audit/x-1: visible + hidden pytest checks in a temp copy (the learner's folder is not
# written to). Last line of stdout: GRADE_TESTS {"passed": N, "total": M}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
audit_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${audit_dir}/_env/grade-pytest.sh" "${ex_dir}" 13 240

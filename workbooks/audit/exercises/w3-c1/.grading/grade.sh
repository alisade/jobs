#!/usr/bin/env bash
# Grade audit/w3-c1: visible + hidden pytest checks in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
audit_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${audit_dir}/_env/grade-pytest.sh" "${ex_dir}" 14 240

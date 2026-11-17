#!/usr/bin/env bash
# Grade backend/w5-c1: visible + hidden go tests (-race) in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track}/_env/grade-go.sh" "${ex_dir}" 180s

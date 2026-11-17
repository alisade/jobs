#!/usr/bin/env bash
# Grade connect/w3-t1: visible + hidden jest tests in a temp copy (the learner's folder is not
# written to; the incident bundle is regenerated there). Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
connect_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${connect_dir}/_env/grade-jest.sh" "${ex_dir}" 15 240

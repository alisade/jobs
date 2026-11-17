#!/usr/bin/env bash
# Grade edgefde/x-2: visible + hidden pytest checks in a temp copy. Last line: GRADE_TESTS {...}.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 13 240

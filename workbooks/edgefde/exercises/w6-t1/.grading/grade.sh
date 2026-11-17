#!/usr/bin/env bash
# Grade edgefde/w6-t1: visible + hidden checks of the site configuration in a temp copy.
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
track_dir="$(cd "${ex_dir}/../.." && pwd)"
exec bash "${track_dir}/_env/grade-pytest.sh" "${ex_dir}" 10 240

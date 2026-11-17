#!/usr/bin/env bash
# Nightly pump-anomaly pipeline, steps 3-4 (train and register ran before this script).
# Usage: ci/pipeline.sh <data_dir> <version>
set -euo pipefail
data="${1:?data dir}"; version="${2:?version}"
py="${PY:-python3}"
echo "== step 3/4 evaluate v${version}"
"${py}" -m ci.evaluate --data "${data}" --model pump-anomaly --version "${version}"
echo "== step 4/4 gate v${version}"
"${py}" -m ci.gate --data "${data}" --model pump-anomaly --challenger "${version}"
echo "== pipeline finished"

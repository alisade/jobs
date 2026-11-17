#!/usr/bin/env bash
# Download (once) the Temporal time-skipping test server into backend/.temporal so the Temporal
# exercises run offline afterwards. Needs the shared venv (ensure-venv.sh). Prints the binary path.
# Idempotent: an existing binary is reused, no network.
set -euo pipefail
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
track="$(cd "${env_dir}/.." && pwd)"
dest="${track}/.temporal"
bash "${env_dir}/ensure-venv.sh" >&2
existing="$(ls "${dest}"/temporal-test-server* 2>/dev/null | head -1 || true)"
if [ -n "${existing}" ] && [ -x "${existing}" ]; then echo "${existing}"; exit 0; fi
mkdir -p "${dest}"
echo "ensure-temporal: downloading the Temporal test server into ${dest} (one time, ~65 MB)" >&2
"${track}/.venv/bin/python" - "${dest}" >&2 <<'PY'
import asyncio, sys
from temporalio.testing import WorkflowEnvironment
async def main(dest):
    env = await WorkflowEnvironment.start_time_skipping(download_dest_dir=dest)
    await env.shutdown()
asyncio.run(main(sys.argv[1]))
PY
existing="$(ls "${dest}"/temporal-test-server* 2>/dev/null | head -1 || true)"
if [ -z "${existing}" ]; then echo "ensure-temporal: download failed" >&2; exit 2; fi
echo "${existing}"

#!/usr/bin/env bash
# Install (once) the shared node toolchain (aws-cdk-lib, jest, ts-jest, typescript) into
# aiarch/_env/node_modules with npm ci, and optionally link it into an exercise folder.
# Usage: ensure-node.sh                 install/refresh only
#        ensure-node.sh link <ex_dir>   install, then symlink <ex_dir>/node_modules -> _env/node_modules
# Idempotent: a stamp of package.json + package-lock.json makes the second run a no-op.
set -euo pipefail
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
stamp="${env_dir}/node_modules/.aiarch-stamp"
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "ensure-node: node/npm not found -> nvm install 22 (see tools/doctor.sh aiarch)" >&2
  exit 2
fi
want="$(cat "${env_dir}/package.json" "${env_dir}/package-lock.json" | shasum | cut -c1-16) $(node --version)"
if [ ! -f "${stamp}" ] || [ "$(cat "${stamp}")" != "${want}" ]; then
  echo "ensure-node: installing shared toolchain into ${env_dir}/node_modules (one time, ~250 MB)" >&2
  (cd "${env_dir}" && npm ci --no-audit --no-fund --loglevel=error >&2)
  echo "${want}" > "${stamp}"
fi
if [ "${1:-}" = "link" ]; then
  ex="${2:?ensure-node.sh link <ex_dir>}"
  if [ -L "${ex}/node_modules" ] || [ ! -e "${ex}/node_modules" ]; then
    ln -sfn "${env_dir}/node_modules" "${ex}/node_modules"
  fi
fi

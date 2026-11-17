#!/usr/bin/env bash
# Build (once) the shared virtualenv for the Python exercises: backend/.venv (uv-managed python).
# Idempotent: a stamp of requirements.txt makes the second run a no-op.
set -euo pipefail
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
venv="$(cd "${env_dir}/.." && pwd)/.venv"
stamp="${venv}/.backend-stamp"
py_version="${BACKEND_PYTHON:-3.12}"
want="$(shasum < "${env_dir}/requirements.txt" | cut -c1-16) ${py_version}"
if [ -f "${stamp}" ] && [ "$(cat "${stamp}")" = "${want}" ] && [ -x "${venv}/bin/python" ]; then exit 0; fi
if ! command -v uv >/dev/null 2>&1; then
  echo "ensure-venv: uv not found -> curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 2
fi
echo "ensure-venv: building ${venv} (python ${py_version})" >&2
uv venv -q --allow-existing -p "${py_version}" "${venv}" >&2
VIRTUAL_ENV="${venv}" uv pip install -q -r "${env_dir}/requirements.txt" >&2
echo "${want}" > "${stamp}"

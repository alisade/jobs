#!/usr/bin/env bash
# Build (once) the shared virtualenv every FDE exercise uses: fde/.venv.
#
# - Python from uv (FDE_PYTHON, default 3.13; the blueprint needs >= 3.11).
# - The blueprint's seven packages installed EDITABLE from COMMERCE_AGENTS
#   (default: <workbooks>/../commerce-agents), using the blueprint's own pinned
#   requirements.txt so versions match the release it was tested with.
#   Nothing is written inside the commerce-agents repo.
# - Test tooling from _env/requirements.txt (pytest, respx, hypothesis, ruff).
# - A .pth file putting the blueprint's examples/ and storefront-mcp-server/ on
#   sys.path, so `from retail.api.mock_retail import MockRetail` works anywhere.
#
# Idempotent: a stamp file records the inputs; a second run is a no-op.
set -euo pipefail

env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
fde_dir="$(cd "${env_dir}/.." && pwd)"
default_ca="$(cd "${fde_dir}/../.." && pwd)/commerce-agents"
ca="${COMMERCE_AGENTS:-${default_ca}}"
venv="${fde_dir}/.venv"
stamp="${venv}/.fde-stamp"
py_version="${FDE_PYTHON:-3.13}"

if [ ! -f "${ca}/requirements.txt" ] || [ ! -d "${ca}/commerce-common" ]; then
  echo "ensure-venv: commerce-agents blueprint not found at ${ca}" >&2
  echo "ensure-venv: clone it there or export COMMERCE_AGENTS=/path/to/commerce-agents" >&2
  exit 2
fi

want="$(cat "${env_dir}/requirements.txt" "${ca}/requirements.txt" | shasum | cut -c1-16) ${ca} ${py_version}"
if [ -f "${stamp}" ] && [ "$(cat "${stamp}")" = "${want}" ] && [ -x "${venv}/bin/python" ]; then
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ensure-venv: uv not found -> curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 2
fi

echo "ensure-venv: building ${venv} (python ${py_version}, blueprint at ${ca})"
uv venv -q --allow-existing -p "${py_version}" "${venv}"

# The blueprint's requirements with its relative editable paths made absolute.
bp_reqs="${venv}/blueprint-requirements.txt"
sed -e "s#^-e \./#-e ${ca}/#" "${ca}/requirements.txt" > "${bp_reqs}"

VIRTUAL_ENV="${venv}" uv pip install -q -r "${bp_reqs}" -r "${env_dir}/requirements.txt"

site="$("${venv}/bin/python" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
{
  echo "${ca}/examples"
  echo "${ca}/shopping-agent/managed-agents/storefront-mcp-server"
} > "${site}/fde_blueprint_paths.pth"

echo "${ca}" > "${venv}/commerce-agents-path"
echo "${want}" > "${stamp}"
echo "ensure-venv: ready ($("${venv}/bin/python" --version))"

#!/usr/bin/env bash
# Report which toolchains the workbooks need and how to install the missing ones.
# Usage: tools/doctor.sh [fde|go|ms|all]   (default: all)
set -u
track="${1:-all}"
missing=0

check() {
  # check <tool> <tracks> <install hint>
  local tool="${1}" tracks="${2}" hint="${3}"
  if [ "${track}" != "all" ] && [[ " ${tracks} " != *" ${track} "* ]]; then return; fi
  if command -v "${tool}" >/dev/null 2>&1; then
    printf '  ok       %-10s (%s)\n' "${tool}" "${tracks}"
  else
    printf '  MISSING  %-10s (%s)  ->  %s\n' "${tool}" "${tracks}" "${hint}"
    missing=$((missing + 1))
  fi
}

echo "Workbook toolchain check (${track})"
check python3 "fde ms"    "brew install python@3.12"
check uv      "fde ms"    "curl -LsSf https://astral.sh/uv/install.sh | sh"
check node    "fde ms"    "nvm install 22"
check go      "go"        "brew install go"
check docker  "optional"  "brew install docker colima (not needed by current exercises)"
check kubectl "optional"  "brew install kubectl (not needed by current exercises)"
check dotnet  "ms"        "brew install --cask dotnet-sdk"
check pac     "optional"  "dotnet tool install --global Microsoft.PowerApps.CLI.Tool (useful for real tenants, not needed by exercises)"
check java    "optional"  "brew install openjdk@17 (not needed by current exercises)"
check jq      "fde go ms" "brew install jq"

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "  ok       docker daemon reachable"
  else
    echo "  WARN     docker daemon not running -> colima start --cpu 4 --memory 8"
  fi
fi

echo
if [ "${missing}" -eq 0 ]; then echo "All tools present."; else echo "${missing} tool(s) missing; install only what your track needs."; fi

#!/usr/bin/env bash
# Run the shared jest for the exercise in the current directory (visible tests). PGlite loads
# its WebAssembly with a dynamic import, which jest only allows with --experimental-vm-modules.
# Usage (from an exercise Makefile): bash <track>/_env/jest.sh [jest args]
set -u
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
NODE_OPTIONS="--experimental-vm-modules --no-warnings" exec "${env_dir}/node_modules/.bin/jest" --ci --forceExit "$@"

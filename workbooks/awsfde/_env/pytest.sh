#!/usr/bin/env bash
# Visible-test runner used by every exercise Makefile (make test): shared venv, fake AWS
# credentials, network blocked by the pytest_offline plugin. Run from the exercise folder.
# Usage: bash ../../_env/pytest.sh [pytest args]   (default: tests)
set -u
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
track_dir="$(cd "${env_dir}/.." && pwd)"
bash "${env_dir}/ensure-venv.sh" || exit 2
export AWS_ACCESS_KEY_ID=testing AWS_SECRET_ACCESS_KEY=testing AWS_SESSION_TOKEN=testing
export AWS_DEFAULT_REGION=us-east-1 AWS_REGION=us-east-1 AWS_EC2_METADATA_DISABLED=true
export AWS_CONFIG_FILE=/dev/null AWS_SHARED_CREDENTIALS_FILE=/dev/null PYTHONDONTWRITEBYTECODE=1
unset AWS_PROFILE
export PYTHONPATH="${env_dir}:$(pwd)${PYTHONPATH:+:${PYTHONPATH}}"
if [ "$#" -eq 0 ]; then set -- tests; fi
exec "${track_dir}/.venv/bin/python" -m pytest -q -p no:cacheprovider -p pytest_offline "$@"

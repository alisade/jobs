#!/usr/bin/env bash
# Download (once) every Maven artifact the Java exercises and their reference solutions use, into
# ~/.m2, so grading can run with mvn -o. Idempotent: a stamp of the prefetch pom skips later runs.
# Usage: ensure-maven.sh [<exercise_dir>]   with a dir, also resolves that exercise's own pom.
set -euo pipefail
env_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
. "${env_dir}/java-env.sh"
stamp="${HOME}/.m2/repository/.modernize-stamp"
want="$(shasum < "${env_dir}/maven-prefetch/pom.xml" | cut -c1-16)"
if [ ! -f "${stamp}" ] || [ "$(cat "${stamp}")" != "${want}" ]; then
  echo "ensure-maven: downloading shared Maven artifacts to ~/.m2 (one time, about a minute)" >&2
  mvn -q -B -f "${env_dir}/maven-prefetch/pom.xml" test >&2
  rm -rf "${env_dir}/maven-prefetch/target"
  mkdir -p "$(dirname "${stamp}")"
  echo "${want}" > "${stamp}"
fi
if [ -n "${1:-}" ] && [ -f "${1}/pom.xml" ]; then
  # resolve the starter's own dependencies and plugins (it may not compile yet: that is the exercise)
  (cd "${1}" && mvn -q -B test-compile >/dev/null 2>&1 || true)
  rm -rf "${1}/target"
fi

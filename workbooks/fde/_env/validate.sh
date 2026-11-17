#!/usr/bin/env bash
# Authoring check for one exercise (or all): the five validations SPEC.md requires.
#   1. make setup works        2. make test runs
#   3. grade.sh on the untouched starter reports failures, last line GRADE_TESTS
#   4. grade.sh on a temp copy with .grading/solution/ overlaid passes every test
#   5. make clean works
# Usage: _env/validate.sh <id> [<id> ...]   or   _env/validate.sh all
set -u
fde_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ids=("$@")
if [ "${#ids[@]}" -eq 0 ] || [ "${ids[0]}" = "all" ]; then
  ids=()
  for d in "${fde_dir}"/exercises/*/; do ids+=("$(basename "${d}")"); done
fi

rc=0
for id in "${ids[@]}"; do
  ex="${fde_dir}/exercises/${id}"
  echo "=== ${id}"
  if [ ! -d "${ex}" ]; then echo "  missing ${ex}"; rc=1; continue; fi

  if make -s -C "${ex}" setup >/tmp/fde-validate-setup.log 2>&1; then echo "  setup:   ok"; else echo "  setup:   FAILED"; tail -20 /tmp/fde-validate-setup.log; rc=1; fi
  make -s -C "${ex}" test >/tmp/fde-validate-test.log 2>&1
  echo "  test:    ran (exit $?) -> $(grep -E 'passed|failed|error' /tmp/fde-validate-test.log | tail -1)"

  out="$(cd "${ex}" && bash .grading/grade.sh 2>&1)"; grc=$?
  last="$(printf '%s\n' "${out}" | tail -1)"
  echo "  starter: exit ${grc} :: ${last}"
  case "${last}" in GRADE_TESTS*) ;; *) echo "  starter: last line is not GRADE_TESTS"; rc=1;; esac
  sp="$(printf '%s' "${last}" | sed -E 's/.*"passed": ([0-9]+).*/\1/')"
  st="$(printf '%s' "${last}" | sed -E 's/.*"total": ([0-9]+).*/\1/')"
  if [ "${sp}" = "${st}" ]; then echo "  starter: NO FAILURES (must fail)"; rc=1; fi

  tmp="$(mktemp -d)"
  rsync -a --exclude .venv --exclude __pycache__ --exclude run --exclude .run "${ex}/" "${tmp}/${id}/"
  rsync -a "${ex}/.grading/solution/" "${tmp}/${id}/"
  # The overlay copy must sit at the same depth so grade.sh finds fde/.venv; link it in.
  mkdir -p "${tmp}/fde/exercises"
  mv "${tmp}/${id}" "${tmp}/fde/exercises/${id}"
  ln -s "${fde_dir}/_env" "${tmp}/fde/_env"
  ln -s "${fde_dir}/.venv" "${tmp}/fde/.venv"
  out2="$(cd "${tmp}/fde/exercises/${id}" && bash .grading/grade.sh 2>&1)"; grc2=$?
  last2="$(printf '%s\n' "${out2}" | tail -1)"
  echo "  solution: exit ${grc2} :: ${last2}"
  sp2="$(printf '%s' "${last2}" | sed -E 's/.*"passed": ([0-9]+).*/\1/')"
  st2="$(printf '%s' "${last2}" | sed -E 's/.*"total": ([0-9]+).*/\1/')"
  if [ "${sp2}" != "${st2}" ]; then echo "  solution: NOT ALL PASSING"; printf '%s\n' "${out2}" | grep -E '^FAIL' | head -10; rc=1; fi
  # Stop anything the overlay copy might have started, then drop it.
  make -s -C "${tmp}/fde/exercises/${id}" clean >/dev/null 2>&1 || true
  rm -rf "${tmp}"

  if make -s -C "${ex}" clean >/tmp/fde-validate-clean.log 2>&1; then echo "  clean:   ok"; else echo "  clean:   FAILED"; tail -5 /tmp/fde-validate-clean.log; rc=1; fi
done
exit "${rc}"

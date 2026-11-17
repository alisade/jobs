#!/usr/bin/env bash
# Authoring check for one exercise (or all): the five validations SPEC.md requires.
#   1. make setup works        2. make test runs
#   3. grade.sh on the untouched starter reports failures, last line GRADE_TESTS
#      (design exercises: reports exactly 0/0 and ships .grading/solution/ANSWER.md)
#   4. grade.sh on a temp copy with .grading/solution/ overlaid passes every test
#   5. make clean works
# Usage: _env/validate.sh <id> [<id> ...]   or   _env/validate.sh all
set -u
track_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ids=("$@")
if [ "${#ids[@]}" -eq 0 ] || [ "${ids[0]}" = "all" ]; then
  ids=()
  for d in "${track_dir}"/exercises/*/; do ids+=("$(basename "${d}")"); done
fi
num() { printf '%s' "${1}" | sed -E "s/.*\"${2}\": ([0-9]+).*/\1/"; }
log="${TMPDIR:-/tmp}/modernize-validate"
mkdir -p "${log}"
rc=0
for id in "${ids[@]}"; do
  ex="${track_dir}/exercises/${id}"
  echo "=== ${id}"
  if [ ! -d "${ex}" ]; then echo "  missing ${ex}"; rc=1; continue; fi
  design=0
  if grep -q 'grade-design.sh' "${ex}/.grading/grade.sh" 2>/dev/null; then design=1; fi

  if make -s -C "${ex}" setup >"${log}/setup.log" 2>&1; then echo "  setup:    ok"; else echo "  setup:    FAILED"; tail -20 "${log}/setup.log"; rc=1; fi
  make -s -C "${ex}" test >"${log}/test.log" 2>&1
  echo "  test:     ran (exit $?) -> $(grep -E 'Tests:|passed|failed|error|GRADE' "${log}/test.log" | tail -1 | cut -c1-110)"

  out="$(cd "${ex}" && bash .grading/grade.sh 2>"${log}/grade.err")"; grc=$?
  last="$(printf '%s\n' "${out}" | tail -1)"
  echo "  starter:  exit ${grc} :: ${last}"
  case "${last}" in GRADE_TESTS*) ;; *) echo "  starter:  last line is not GRADE_TESTS"; tail -5 "${log}/grade.err"; rc=1;; esac
  sp="$(num "${last}" passed)"; st="$(num "${last}" total)"
  if [ "${design}" -eq 1 ]; then
    if [ "${st}" != "0" ]; then echo "  starter:  design exercise must report 0/0"; rc=1; fi
    if [ ! -f "${ex}/.grading/solution/ANSWER.md" ]; then echo "  solution: design exercise needs .grading/solution/ANSWER.md"; rc=1; fi
  elif [ "${sp}" = "${st}" ]; then echo "  starter:  NO FAILURES (must fail)"; rc=1; fi

  tmp="$(mktemp -d)"
  mkdir -p "${tmp}/modernize/exercises"
  rsync -a --exclude node_modules --exclude .venv --exclude __pycache__ --exclude cdk.out --exclude target --exclude coverage --exclude incident --exclude bin --exclude obj "${ex}/" "${tmp}/modernize/exercises/${id}/"
  rsync -a "${ex}/.grading/solution/" "${tmp}/modernize/exercises/${id}/"
  ln -s "${track_dir}/_env" "${tmp}/modernize/_env"
  [ -d "${track_dir}/.venv" ] && ln -s "${track_dir}/.venv" "${tmp}/modernize/.venv"
  if [ "${design}" -eq 0 ]; then make -s -C "${tmp}/modernize/exercises/${id}" setup >/dev/null 2>&1 || true; fi
  out2="$(cd "${tmp}/modernize/exercises/${id}" && bash .grading/grade.sh 2>/dev/null)"; grc2=$?
  last2="$(printf '%s\n' "${out2}" | tail -1)"
  echo "  solution: exit ${grc2} :: ${last2}"
  sp2="$(num "${last2}" passed)"; st2="$(num "${last2}" total)"
  if [ "${sp2}" != "${st2}" ]; then echo "  solution: NOT ALL PASSING"; printf '%s\n' "${out2}" | grep -E '^(FAIL|HARNESS)' | head -10; rc=1; fi
  make -s -C "${tmp}/modernize/exercises/${id}" clean >/dev/null 2>&1 || true
  rm -rf "${tmp}"

  if make -s -C "${ex}" clean >"${log}/clean.log" 2>&1; then echo "  clean:    ok"; else echo "  clean:    FAILED"; tail -5 "${log}/clean.log"; rc=1; fi
done
exit "${rc}"

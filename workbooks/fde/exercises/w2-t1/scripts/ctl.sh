#!/usr/bin/env bash
# Start / stop the local incident environment: fake IdP (:18210), edge-mcp-gateway
# (:18211), upstream MCP stub (:18212). PIDs and logs live in run/.
#   scripts/ctl.sh start | stop | status | restart-gateway
set -u
ex_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fde_dir="$(cd "${ex_dir}/../.." && pwd)"
py="${fde_dir}/.venv/bin/python"
run="${ex_dir}/run"
IDP_PORT=18210
GW_PORT=18211
UP_PORT=18212

wait_ready() {
  # wait_ready <name> <url>: up to ~15 s
  local name="${1}" url="${2}" i code
  for i in $(seq 1 30); do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 1 "${url}" 2>/dev/null || true)"
    if [ -n "${code}" ] && [ "${code}" != "000" ]; then return 0; fi
    sleep 0.5
  done
  echo "${name} did not become ready at ${url}; see run/${name}.log" >&2
  return 1
}

start_one() {
  # start_one <name> <port> <uvicorn target...>
  local name="${1}" port="${2}"
  shift 2
  ( cd "${ex_dir}" && nohup "${py}" -m uvicorn "$@" --host 127.0.0.1 --port "${port}" \
      --no-access-log >>"${run}/${name}.log" 2>&1 & echo $! >"${run}/${name}.pid" )
}

stop_one() {
  local name="${1}" pid
  if [ -f "${run}/${name}.pid" ]; then
    pid="$(cat "${run}/${name}.pid")"
    if kill -0 "${pid}" 2>/dev/null; then
      kill "${pid}" 2>/dev/null
      for _ in $(seq 1 20); do kill -0 "${pid}" 2>/dev/null || break; sleep 0.25; done
      kill -9 "${pid}" 2>/dev/null || true
    fi
    rm -f "${run}/${name}.pid"
  fi
}

free_port() {
  # A stale process from an earlier run that lost its pid file.
  local port="${1}" pids
  pids="$(lsof -ti "tcp:${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "${pids}" ]; then kill ${pids} 2>/dev/null || true; sleep 0.5; fi
}

case "${1:-}" in
  start)
    mkdir -p "${run}"
    for n in gateway idp upstream; do stop_one "${n}"; done
    for p in "${IDP_PORT}" "${GW_PORT}" "${UP_PORT}"; do free_port "${p}"; done
    start_one upstream "${UP_PORT}" gateway.upstream:app
    start_one idp "${IDP_PORT}" gateway.idp:app
    wait_ready upstream "http://127.0.0.1:${UP_PORT}/mcp" || exit 1
    wait_ready idp "http://127.0.0.1:${IDP_PORT}/admin/state" || exit 1
    start_one gateway "${GW_PORT}" --factory gateway.serve:app_factory
    wait_ready gateway "http://127.0.0.1:${GW_PORT}/healthz" || exit 1
    ;;
  restart-gateway)
    stop_one gateway
    free_port "${GW_PORT}"
    start_one gateway "${GW_PORT}" --factory gateway.serve:app_factory
    wait_ready gateway "http://127.0.0.1:${GW_PORT}/healthz" || exit 1
    echo "gateway restarted"
    ;;
  stop)
    for n in gateway idp upstream; do stop_one "${n}"; done
    for p in "${IDP_PORT}" "${GW_PORT}" "${UP_PORT}"; do free_port "${p}"; done
    ;;
  status)
    for n in idp gateway upstream; do
      if [ -f "${run}/${n}.pid" ] && kill -0 "$(cat "${run}/${n}.pid")" 2>/dev/null; then
        echo "${n}: running (pid $(cat "${run}/${n}.pid"))"
      else
        echo "${n}: stopped"
      fi
    done
    ;;
  *)
    echo "usage: scripts/ctl.sh start|stop|status|restart-gateway" >&2
    exit 2
    ;;
esac

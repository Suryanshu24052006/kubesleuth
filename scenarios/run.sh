#!/usr/bin/env bash
# Usage: scenarios/run.sh <scenario-id> inject|revert|describe
#        scenarios/run.sh reset            restore the healthy baseline
#        scenarios/run.sh list
set -euo pipefail
cd "$(dirname "$0")"
NS=shop
log() { printf '\033[1;33m[scenario]\033[0m %s\n' "$*"; }
export NS

reset() {
  log "restoring baseline"
  kubectl -n "$NS" delete networkchaos --all --ignore-not-found >/dev/null 2>&1 || true
  kubectl -n "$NS" delete deploy pricing-legacy --ignore-not-found
  kubectl -n "$NS" delete svc telemetry-collector-v2 --ignore-not-found
  # Remember what needs a restart BEFORE restoring: only restart what a scenario actually changed.
  # (Restarting everything at once overloads a small node and becomes noise in the next scenario.)
  local pool restarts
  pool=$(kubectl -n "$NS" get configmap checkout-config -o jsonpath='{.data.DB_POOL_SIZE}' 2>/dev/null)
  restarts=$(kubectl -n "$NS" get pods -l app=recommendations \
    -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' 2>/dev/null | awk '{s+=$1} END {print s+0}')
  # Restores ConfigMaps (WAF rules and flags hot-reload), replica counts and pod templates (probes roll out).
  kubectl apply -k ../deploy/shop >/dev/null
  if [ "$pool" != "4" ]; then
    log "checkout reads DB_POOL_SIZE at start-up: restarting checkout"
    kubectl -n "$NS" rollout restart deploy/checkout >/dev/null
  fi
  if [ "${restarts:-0}" -gt 0 ]; then
    log "recommendations crashed during the scenario: restarting it to clear its buffer"
    kubectl -n "$NS" rollout restart deploy/recommendations >/dev/null
  fi
  for d in $(kubectl -n "$NS" get deploy -o name); do
    kubectl -n "$NS" rollout status "$d" --timeout=240s >/dev/null
  done
  log "baseline restored; give metrics ~3 minutes to settle before the next scenario"
}

case "${1:-}" in
  list) for d in */; do printf '%-34s %s\n' "${d%/}" "$(grep -m1 '^title:' "$d/scenario.yaml" | cut -d: -f2-)"; done ;;
  reset) reset ;;
  "") echo "usage: $0 <id> inject|revert|describe | reset | list"; exit 1 ;;
  *)
    id="$1"; action="${2:-inject}"
    [ -d "$id" ] || { echo "unknown scenario $id"; exit 1; }
    case "$action" in
      inject) log "injecting $id"; bash "$id/inject.sh" ;;
      revert) reset ;;
      describe) cat "$id/scenario.yaml" ;;
      *) echo "unknown action $action"; exit 1 ;;
    esac ;;
esac

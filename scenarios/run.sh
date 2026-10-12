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
  kubectl apply -k ../deploy/shop >/dev/null
  # config-only changes need a restart to be picked up the same way they were broken
  kubectl -n "$NS" rollout restart deploy/checkout deploy/edge deploy/recommendations deploy/inventory >/dev/null
  for d in checkout edge recommendations inventory pricing catalog-indexer; do
    kubectl -n "$NS" rollout status "deploy/$d" --timeout=240s >/dev/null
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

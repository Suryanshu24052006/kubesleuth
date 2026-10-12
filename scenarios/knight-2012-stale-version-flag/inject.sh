#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "$0")"
echo "1/2 the forgotten legacy deployment is (already) running behind the pricing Service"
kubectl apply -f "$here/pricing-legacy.yaml"
kubectl -n "$NS" rollout status deploy/pricing-legacy --timeout=120s
sleep 45
echo "2/2 product turns on the repurposed flag"
kubectl -n "$NS" create configmap feature-flags --dry-run=client -o yaml \
  --from-literal=flags.json='{"smart_routing": true, "new_checkout_ui": true}' | kubectl apply -f -

#!/usr/bin/env bash
set -euo pipefail
echo "a 'performance tuning' change: bigger DB pool for checkout"
kubectl -n "$NS" patch configmap checkout-config --type merge -p '{"data":{"DB_POOL_SIZE":"30"}}'
kubectl -n "$NS" rollout restart deploy/checkout

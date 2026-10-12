#!/usr/bin/env bash
set -euo pipefail
echo "intended: kubectl -n shop scale deploy -l app=catalog-indexer --replicas=1"
echo "executed: kubectl -n shop scale deploy -l tier=backend --replicas=1   (typo'd selector)"
kubectl -n "$NS" scale deploy -l tier=backend --replicas=1

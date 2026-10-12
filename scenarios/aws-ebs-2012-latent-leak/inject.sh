#!/usr/bin/env bash
set -euo pipefail
echo "migrating the telemetry collector to a new Service name (clients are not updated)"
kubectl -n "$NS" create service clusterip telemetry-collector-v2 --tcp=8080:8080 --dry-run=client -o yaml \
  | sed 's/app: telemetry-collector-v2/app: telemetry-collector/' | kubectl apply -f -
kubectl -n "$NS" delete service telemetry-collector
echo "recommendations now buffers telemetry in memory; expect OOMKilled in ~3-6 minutes"

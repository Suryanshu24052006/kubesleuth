#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "$0")"
echo "1/2 'hardening' the checkout liveness probe"
kubectl -n "$NS" patch deploy checkout --type json -p '[
 {"op":"replace","path":"/spec/template/spec/containers/0/livenessProbe","value":
   {"httpGet":{"path":"/healthz?deep=1","port":"http"},"periodSeconds":5,"timeoutSeconds":1,"failureThreshold":1}}]'
kubectl -n "$NS" rollout status deploy/checkout --timeout=180s
sleep 60
echo "2/2 Chaos Mesh: Postgres gets ~850ms of network latency (a tolerable degradation on its own)"
kubectl apply -f "$here/postgres-latency.yaml"

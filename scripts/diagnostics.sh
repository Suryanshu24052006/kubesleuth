#!/usr/bin/env bash
# Dumps cluster state for debugging a failed run: pods, events, Helm releases, logs.
# Usage: scripts/diagnostics.sh <output-dir>
set -uo pipefail
out=${1:-diagnostics}
mkdir -p "$out"
kubectl get nodes -o wide > "$out/nodes.txt" 2>&1
kubectl get pods -A -o wide > "$out/pods.txt" 2>&1
kubectl get events -A --sort-by=.lastTimestamp > "$out/events.txt" 2>&1
helm list -A > "$out/helm.txt" 2>&1
kubectl -n shop get deploy,sts,svc,endpointslices,hpa,pvc,ingress,httproute,configmap -o wide > "$out/shop-objects.txt" 2>&1
kubectl top pods -A > "$out/top-pods.txt" 2>&1
for ns in shop kubesleuth observability monitoring traefik chaos-mesh; do
  for p in $(kubectl -n "$ns" get pods -o name 2>/dev/null); do
    name=${p#pod/}
    kubectl -n "$ns" logs "$p" --all-containers --tail=300 > "$out/logs-$ns-$name.txt" 2>&1
    kubectl -n "$ns" logs "$p" --all-containers --previous --tail=200 > "$out/logs-$ns-$name.previous.txt" 2>/dev/null \
      || rm -f "$out/logs-$ns-$name.previous.txt"
  done
done
# non-running pods in detail
kubectl get pods -A --no-headers 2>/dev/null | awk '$4!="Running" && $4!="Completed" {print $1" "$2}' | while read -r ns pod; do
  kubectl -n "$ns" describe pod "$pod" > "$out/describe-$ns-$pod.txt" 2>&1
done
echo "diagnostics written to $out"

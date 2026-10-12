#!/usr/bin/env bash
# Port-forwards for local use. Ctrl-C stops them all.
trap 'kill 0' EXIT
kubectl -n monitoring port-forward svc/kps-grafana 3000:80 >/dev/null &
kubectl -n monitoring port-forward svc/kps-prometheus 9090:9090 >/dev/null &
kubectl -n monitoring port-forward svc/kps-alertmanager 9093:9093 >/dev/null &
kubectl -n observability port-forward svc/jaeger 16686:16686 >/dev/null &
kubectl -n kubesleuth port-forward svc/kubesleuth-broker 8090:8090 >/dev/null &
kubectl -n kubesleuth port-forward svc/kubesleuth-agent 8081:8080 >/dev/null &
echo "Grafana http://localhost:3000 (admin/kubesleuth) | Prometheus :9090 | Alertmanager :9093 | Jaeger :16686"
echo "broker MCP http://localhost:8090/mcp | agent reports http://localhost:8081"
wait

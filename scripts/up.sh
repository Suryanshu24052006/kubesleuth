#!/usr/bin/env bash
# Creates the kind cluster and installs everything. Idempotent: safe to re-run.
set -euo pipefail
cd "$(dirname "$0")/.."
CLUSTER=kubesleuth
log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

for bin in docker kind kubectl helm; do
  command -v "$bin" >/dev/null || { echo "missing prerequisite: $bin (see README > Prerequisites)"; exit 1; }
done

if ! kind get clusters | grep -qx "$CLUSTER"; then
  log "creating kind cluster '$CLUSTER'"
  kind create cluster --config cluster/kind-config.yaml --wait 120s
fi
kubectl config use-context "kind-$CLUSTER" >/dev/null

log "Gateway API CRDs (v1.3.0)"
kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml >/dev/null

log "helm repositories"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null 2>&1 || true
helm repo add grafana https://grafana.github.io/helm-charts >/dev/null 2>&1 || true
helm repo add traefik https://traefik.github.io/charts >/dev/null 2>&1 || true
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null 2>&1 || true
helm repo add chaos-mesh https://charts.chaos-mesh.org >/dev/null 2>&1 || true
helm repo update >/dev/null

log "kube-prometheus-stack (Prometheus, Alertmanager, Grafana, kube-state-metrics)"
helm upgrade --install kps prometheus-community/kube-prometheus-stack --version 75.15.1 \
  -n monitoring --create-namespace -f cluster/helm/kube-prometheus-stack.yaml --wait --timeout 10m
log "Loki + Alloy (logs)"
helm upgrade --install loki grafana/loki --version 6.30.1 -n observability --create-namespace \
  -f cluster/helm/loki.yaml --wait --timeout 10m
helm upgrade --install alloy grafana/alloy --version 1.1.2 -n observability -f cluster/helm/alloy.yaml --wait
log "Jaeger (traces)"
kubectl apply -f deploy/observability/jaeger.yaml
log "Traefik (Ingress + Gateway API), metrics-server (HPA), Chaos Mesh"
helm upgrade --install traefik traefik/traefik --version 36.3.0 -n traefik --create-namespace \
  -f cluster/helm/traefik.yaml --wait
helm upgrade --install metrics-server metrics-server/metrics-server --version 3.12.2 -n kube-system \
  -f cluster/helm/metrics-server.yaml --wait
helm upgrade --install chaos-mesh chaos-mesh/chaos-mesh --version 2.7.2 -n chaos-mesh --create-namespace \
  -f cluster/helm/chaos-mesh.yaml --wait --timeout 10m

log "building images"
docker build -q -t shop:1.4.0 --build-arg APP_VERSION=1.4.0 shop/
docker build -q -t shop:0.9.7 --build-arg APP_VERSION=0.9.7 shop/      # the "forgotten" legacy build
docker build -q -t kubesleuth-broker:0.1.0 broker/
docker build -q -t kubesleuth-agent:0.1.0 agent/
kind load docker-image --name "$CLUSTER" shop:1.4.0 shop:0.9.7 kubesleuth-broker:0.1.0 kubesleuth-agent:0.1.0

log "deploying the shop and kubesleuth"
kubectl apply -k deploy/shop
kubectl apply -k deploy/kubesleuth
./scripts/llm-secret.sh || true
kubectl -n shop rollout status statefulset/postgres --timeout=180s
for d in $(kubectl -n shop get deploy -o name); do kubectl -n shop rollout status "$d" --timeout=180s; done
kubectl -n kubesleuth rollout status deploy/kubesleuth-broker --timeout=120s
kubectl -n kubesleuth rollout status deploy/kubesleuth-agent --timeout=120s

log "ready"
cat <<MSG
  shop (via Traefik Ingress):  curl -s 'http://shop.localhost:8080/?q=tent'
  Gateway API route:           curl -s -H 'Host: gw.shop.localhost' http://localhost:8080/?q=tent
  port-forwards:               make ports   (Grafana :3000 admin/kubesleuth, Prometheus :9090, broker :8090, agent :8081)
  break something:             make scenario S=github-conn-saturation
  investigate:                 make investigate
MSG

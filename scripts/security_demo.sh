#!/usr/bin/env bash
# Demonstrates the agent's security boundary on the live cluster. Every line is a check
# with an expected outcome; the script exits non-zero if any boundary is NOT enforced.
set -uo pipefail
cd "$(dirname "$0")/.."
FAIL=0
pass() { printf '  \033[32mPASS\033[0m %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m %s\n' "$*"; FAIL=1; }
SA=system:serviceaccount:kubesleuth:kubesleuth-broker

echo "1) RBAC: what can the broker's identity do? (kubectl auth can-i --as $SA)"
check() { # expected verb resource namespace
  local exp=$1 verb=$2 res=$3 ns=$4 got
  got=$(kubectl auth can-i "$verb" "$res" ${ns:+-n "$ns"} --as "$SA" 2>/dev/null)
  [ "$got" = "$exp" ] && pass "$verb $res ${ns:+in $ns} -> $got" || fail "$verb $res ${ns:+in $ns} -> $got (expected $exp)"
}
check yes list pods shop
check yes get pods/log shop
check yes watch deployments.apps shop
check yes list nodes ""
check no  get secrets shop
check no  create pods/exec shop
check no  create pods/portforward shop
check no  delete pods shop
check no  patch deployments.apps shop
check no  update configmaps shop
check no  create deployments.apps shop
check no  list pods kube-system
check no  list pods kubesleuth
check no  get secrets kube-system

echo "2) The agent pod holds no Kubernetes credentials"
AGENT=$(kubectl -n kubesleuth get pod -l app=kubesleuth-agent -o jsonpath='{.items[0].metadata.name}')
if kubectl -n kubesleuth exec "$AGENT" -- python -c "import os,sys; sys.exit(os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount/token'))"; then
  pass "no service-account token mounted in $AGENT"
else
  fail "service-account token is mounted in the agent pod"
fi
kubectl -n kubesleuth exec "$AGENT" -- python -c "import kubernetes" 2>/dev/null \
  && fail "kubernetes client library present in agent image" || pass "kubernetes client library not even installed in the agent image"

echo "3) Network: the agent can reach the broker and nothing else in the cluster"
probe() { # expected(ok|blocked) url
  local exp=$1 url=$2 out
  out=$(kubectl -n kubesleuth exec "$AGENT" -- python -c "
import httpx,sys
try:
    r=httpx.get('$url',timeout=4,verify=False); print('ok', r.status_code)
except Exception as e: print('blocked', type(e).__name__)" 2>&1 | tail -1)
  case "$out" in "$exp"*) pass "$url -> $out";; *) fail "$url -> $out (expected $exp)";; esac
}
probe ok      http://kubesleuth-broker:8090/healthz
probe blocked https://kubernetes.default.svc/api
probe blocked http://kps-prometheus.monitoring.svc:9090/-/healthy
probe blocked http://loki.observability.svc:3100/ready
probe blocked http://postgres.shop.svc:5432/
echo "  (if the 'blocked' checks fail, your CNI does not enforce NetworkPolicy; kind >= v0.24 kindnet does)"

echo "4) Broker policy: a hijacked agent attacking through MCP"
kubectl -n kubesleuth port-forward svc/kubesleuth-broker 18091:8090 >/dev/null 2>&1 & PF=$!
sleep 3
PYTHONPATH=agent python -m kubesleuth_agent.security_probe --broker http://127.0.0.1:18091/mcp || FAIL=1
kill $PF 2>/dev/null

echo "5) Audit trail (last denied calls, from the broker log)"
kubectl -n kubesleuth logs deploy/kubesleuth-broker --tail=400 | grep kubesleuth.audit | grep '"outcome": "denied"' | tail -5 \
  | sed 's/^/    /' || true

echo "6) Prompt injection: review-bot logs injection payloads continuously; see the 'Security notes'"
echo "   section of any report (e.g. make investigate) — payloads are flagged and never acted upon."
[ $FAIL -eq 0 ] && echo -e "\nALL BOUNDARY CHECKS PASSED" || { echo -e "\nSOME CHECKS FAILED"; exit 1; }

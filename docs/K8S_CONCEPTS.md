# Kubernetes concepts used in this repo (and how each one breaks)

The mentor checklist, mapped to concrete objects here, commands to try on the kind cluster, and the
scenario where that concept is the failure point.

| Concept | Where in the repo | Try it | Breaks in |
|---|---|---|---|
| **Pod** | every shop container; `kubectl -n shop get pods -o wide` | `kubectl -n shop describe pod <pod>` → read *Last State*, *Events* | EBS (OOMKilled loop), Chef (liveness kills) |
| **ReplicaSet** | created by each Deployment rollout | `kubectl -n shop get rs -l app=checkout` → one RS per revision | GitHub/Chef (new RS = new revision, the agent diffs them) |
| **Deployment** | `deploy/shop/3x-*.yaml` | `kubectl -n shop rollout history deploy/checkout`; `rollout undo` | Knight (a second Deployment with the same labels) |
| **StatefulSet + PVC** | `deploy/shop/20-postgres.yaml` (volumeClaimTemplates, kind's `standard` StorageClass) | `kubectl -n shop get pvc`; delete `postgres-0` and watch data survive | GitHub (Postgres `max_connections`) |
| **Service / ClusterIP** | one per workload; selector `app: <name>` | `kubectl -n shop get endpointslices -l kubernetes.io/service-name=pricing` | Knight (Service selects old + new pods), EBS (Service renamed, clients keep old DNS name) |
| **Ingress** | `deploy/shop/40-ingress.yaml`, Traefik controller | `curl 'http://shop.localhost:8080/?q=tent'` | loadgen enters through it, so edge 5xx is what users see |
| **Gateway API** (bonus) | `HTTPRoute` in the same file, Traefik's default Gateway | `curl -H 'Host: gw.shop.localhost' localhost:8080/` | — |
| **HorizontalPodAutoscaler** | `edge` HPA (CPU 70%, 2→3), needs metrics-server | `kubectl -n shop get hpa -w` during the Cloudflare scenario | Cloudflare (HPA maxes out: a symptom, not the fix) |
| **Probes** | liveness/readiness on every Deployment | `kubectl -n shop get events --field-selector reason=Unhealthy` | Chef (aggressive deep liveness probe) |
| **Resource requests/limits** | every container | `kubectl top pods -n shop` | S3 (CPU throttling at 250m), EBS (memory limit 192Mi) |
| **ConfigMap (env vs mounted)** | `checkout-config` (env, needs restart) vs `edge-waf-rules`/`feature-flags` (volume, hot-reloaded) | edit one and watch the pod log `configuration reloaded` | Cloudflare, Knight, GitHub |
| **RBAC** | `deploy/kubesleuth/10-rbac.yaml` | `kubectl auth can-i get secrets -n shop --as system:serviceaccount:kubesleuth:kubesleuth-broker` | the security boundary |
| **NetworkPolicy** | `deploy/kubesleuth/40-networkpolicy.yaml` | `make security-demo` | the security boundary |
| **Helm** | `scripts/up.sh` + `cluster/helm/*.yaml` (pinned versions) | `helm list -A`; `helm get values kps -n monitoring` | — |
| **Watch / informers** | `broker/kubesleuth_broker/journal.py` | `kubectl -n shop get cm -w` in one terminal, edit a ConfigMap in another | how the agent sees diffs |

## Check yourself

1. A Deployment has 3 ready replicas but the Service returns errors 1/3 of the time. Name two
   Kubernetes-level causes and the command that distinguishes them.
2. Why does editing `checkout-config` do nothing until a rollout, while editing `feature-flags` takes
   effect within about a minute?
3. A container restarted 12 times. How do you tell OOMKilled from a liveness-probe kill, and where do
   you read the logs from *before* the restart?
4. The edge HPA sits at maxReplicas and latency is still high. Why is "add more replicas" the wrong
   conclusion in the Cloudflare scenario?
5. The broker's ServiceAccount can `list pods` in `shop`. What two independent things stop it from
   listing pods in `kube-system`?

<details><summary>Answers</summary>

1. Two workloads behind one selector (compare `backing_workloads`/images per pod: Knight), or one bad
   pod/ReplicaSet mid-rollout (compare `rollout history` and per-pod error metrics).
   `kubectl get pods -l app=pricing -L track -o wide` plus errors by pod.
2. Env vars are read once at container start; mounted ConfigMaps are updated in place by the kubelet
   (after its sync period) and the app re-reads the file.
3. `kubectl describe pod` → *Last State: Terminated, Reason: OOMKilled* vs events
   *Liveness probe failed … will be restarted*; logs from before: `kubectl logs --previous`.
4. The CPU is burned by a pathological regex per request; more replicas burn more CPU on the same
   work. The fix is reverting the rule.
5. RBAC (RoleBinding only in `shop`) and the broker's namespace policy, plus the agent having no
   credentials and no network path to the API server at all.
</details>

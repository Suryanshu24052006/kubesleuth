"""Read-only access to the Kubernetes API.

Objects are returned as plain dicts in the same shape `kubectl get -o json`
produces, so the live client and the offline fixtures are interchangeable.
There is intentionally no method here that can create, update, delete, exec
or read Secrets.
"""
from __future__ import annotations

from typing import Protocol


class KubeSource(Protocol):
    def list(self, kind: str, namespace: str | None) -> list[dict]: ...
    def get(self, kind: str, namespace: str | None, name: str) -> dict | None: ...
    def logs(self, namespace: str, pod: str, container: str | None, previous: bool,
             tail: int, since_seconds: int | None) -> str: ...


class LiveKube:
    def __init__(self):
        from kubernetes import client, config

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        api = client.ApiClient()
        self._ser = api.sanitize_for_serialization
        core, apps = client.CoreV1Api(api), client.AppsV1Api(api)
        autoscaling, net = client.AutoscalingV2Api(api), client.NetworkingV1Api(api)
        disc = client.DiscoveryV1Api(api)
        self._core = core
        # kind -> (namespaced list, namespaced read)
        self._ops = {
            "pod": (core.list_namespaced_pod, core.read_namespaced_pod),
            "service": (core.list_namespaced_service, core.read_namespaced_service),
            "configmap": (core.list_namespaced_config_map, core.read_namespaced_config_map),
            "pvc": (core.list_namespaced_persistent_volume_claim, core.read_namespaced_persistent_volume_claim),
            "event": (core.list_namespaced_event, core.read_namespaced_event),
            "deployment": (apps.list_namespaced_deployment, apps.read_namespaced_deployment),
            "replicaset": (apps.list_namespaced_replica_set, apps.read_namespaced_replica_set),
            "statefulset": (apps.list_namespaced_stateful_set, apps.read_namespaced_stateful_set),
            "daemonset": (apps.list_namespaced_daemon_set, apps.read_namespaced_daemon_set),
            "hpa": (autoscaling.list_namespaced_horizontal_pod_autoscaler,
                    autoscaling.read_namespaced_horizontal_pod_autoscaler),
            "ingress": (net.list_namespaced_ingress, net.read_namespaced_ingress),
            "networkpolicy": (net.list_namespaced_network_policy, net.read_namespaced_network_policy),
            "endpointslice": (disc.list_namespaced_endpoint_slice, disc.read_namespaced_endpoint_slice),
        }
        self._cluster_ops = {"node": (core.list_node, core.read_node)}

    def list(self, kind: str, namespace: str | None) -> list[dict]:
        if kind in self._cluster_ops:
            return self._ser(self._cluster_ops[kind][0]()).get("items", [])
        return self._ser(self._ops[kind][0](namespace)).get("items", [])

    def get(self, kind: str, namespace: str | None, name: str) -> dict | None:
        from kubernetes.client.exceptions import ApiException
        try:
            if kind in self._cluster_ops:
                return self._ser(self._cluster_ops[kind][1](name))
            return self._ser(self._ops[kind][1](name, namespace))
        except ApiException as exc:
            if exc.status == 404:
                return None
            raise

    def logs(self, namespace, pod, container, previous, tail, since_seconds):
        from kubernetes.client.exceptions import ApiException
        kw = {"tail_lines": tail, "previous": previous, "timestamps": True}
        if container:
            kw["container"] = container
        if since_seconds:
            kw["since_seconds"] = since_seconds
        try:
            return self._core.read_namespaced_pod_log(pod, namespace, **kw)
        except ApiException as exc:
            if exc.status in (400, 404):
                return f"[no logs available: {exc.reason}: {(exc.body or '')[:200]}]"
            raise

    # used by the change journal
    def watch_targets(self):
        return {k: self._ops[k][0] for k in ("deployment", "statefulset", "configmap", "service", "hpa")}


class FixtureKube:
    """Serves objects from a recorded snapshot (see fixtures.py)."""

    def __init__(self, objects: dict[str, list[dict]], logs: dict[str, str]):
        self._objects = objects
        self._logs = logs

    def list(self, kind, namespace):
        return [o for o in self._objects.get(kind, [])
                if namespace is None or o.get("metadata", {}).get("namespace") in (namespace, None)]

    def get(self, kind, namespace, name):
        for o in self.list(kind, namespace):
            if o["metadata"]["name"] == name:
                return o
        return None

    def logs(self, namespace, pod, container, previous, tail, since_seconds):
        keys = [f"{namespace}/{pod}/{container or ''}/{'previous' if previous else 'current'}",
                f"{namespace}/{pod}//{'previous' if previous else 'current'}"]
        for k in keys:
            if k in self._logs:
                return "\n".join(self._logs[k].splitlines()[-tail:])
        return "[no logs available: previous terminated container not found]" if previous else ""

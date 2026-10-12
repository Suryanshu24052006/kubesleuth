"""Authorization policy for every tool call.

The broker is the only component holding cluster credentials, so it is also the
place where the investigation scope is enforced. RBAC (deploy/kubesleuth/rbac.yaml)
is the second, independent layer: even if this module had a bug, the service
account can only get/list/watch inside the allowed namespaces.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


class PolicyError(Exception):
    """Raised when a request falls outside the investigation boundary."""


DNS_LABEL = re.compile(r"^[a-z0-9]([-a-z0-9]{0,61}[a-z0-9])?$")
DNS_SUBDOMAIN = re.compile(r"^[a-z0-9]([-a-z0-9.]{0,251}[a-z0-9])?$")

# Kinds the agent may read. Secrets are deliberately absent (and absent from RBAC).
NAMESPACED_KINDS = {
    "pod", "deployment", "replicaset", "statefulset", "daemonset", "service",
    "configmap", "pvc", "hpa", "ingress", "networkpolicy", "endpointslice", "event",
}
CLUSTER_KINDS = {"node"}

# Metrics that are not namespaced and are safe to read cluster-wide.
CLUSTER_METRIC_PREFIXES = ("node_", "kube_node_", "machine_")

_SELECTOR = re.compile(r"([a-zA-Z_:][a-zA-Z0-9_:]*)?\s*\{([^{}]*)\}")
_BARE_RANGE = re.compile(r"(?<![\w:}])([a-zA-Z_:][a-zA-Z0-9_:]*)\s*\[")
_NS_MATCHER = re.compile(r'namespace\s*(=~|!~|!=|=)\s*"([^"]*)"')
_PROMQL_KEYWORDS = {"by", "without", "on", "ignoring", "group_left", "group_right", "offset", "bool",
                    "and", "or", "unless", "inf", "nan", "Inf", "NaN",
                    "sum", "avg", "min", "max", "count", "group", "stddev", "stdvar", "topk", "bottomk",
                    "quantile", "count_values", "limitk", "limit_ratio"}


@dataclass(frozen=True)
class Policy:
    allowed_namespaces: frozenset[str] = field(default_factory=lambda: frozenset({"shop"}))
    max_window_minutes: int = 360
    max_promql_length: int = 800
    max_log_lines: int = 2000

    @classmethod
    def from_env(cls) -> "Policy":
        ns = os.environ.get("ALLOWED_NAMESPACES", "shop")
        return cls(allowed_namespaces=frozenset(n.strip() for n in ns.split(",") if n.strip()))

    # ------------------------------------------------------------------ identifiers
    def namespace(self, ns: str) -> str:
        if not isinstance(ns, str) or not DNS_LABEL.match(ns):
            raise PolicyError(f"invalid namespace {ns!r}")
        if ns not in self.allowed_namespaces:
            raise PolicyError(
                f"namespace {ns!r} is outside the investigation scope "
                f"(allowed: {', '.join(sorted(self.allowed_namespaces))})")
        return ns

    @staticmethod
    def name(value: str, what: str = "name") -> str:
        if not isinstance(value, str) or not DNS_SUBDOMAIN.match(value):
            raise PolicyError(f"invalid {what} {value!r}")
        return value

    @staticmethod
    def kind(kind: str) -> str:
        k = (kind or "").strip().lower()
        aliases = {
            "deploy": "deployment", "deployments": "deployment", "svc": "service", "services": "service",
            "cm": "configmap", "configmaps": "configmap", "po": "pod", "pods": "pod",
            "rs": "replicaset", "replicasets": "replicaset", "sts": "statefulset", "statefulsets": "statefulset",
            "ds": "daemonset", "daemonsets": "daemonset", "ing": "ingress", "ingresses": "ingress",
            "horizontalpodautoscaler": "hpa", "horizontalpodautoscalers": "hpa",
            "persistentvolumeclaim": "pvc", "persistentvolumeclaims": "pvc",
            "netpol": "networkpolicy", "networkpolicies": "networkpolicy",
            "endpoints": "endpointslice", "endpointslices": "endpointslice", "events": "event",
            "nodes": "node", "no": "node", "secrets": "secret", "serviceaccounts": "serviceaccount",
        }
        k = aliases.get(k, k)
        if k in ("secret", "serviceaccount", "token"):
            raise PolicyError(f"reading {kind!r} objects is not permitted for the investigation agent")
        if k not in NAMESPACED_KINDS | CLUSTER_KINDS:
            raise PolicyError(f"unsupported kind {kind!r}; allowed: "
                              f"{', '.join(sorted(NAMESPACED_KINDS | CLUSTER_KINDS))}")
        return k

    def minutes(self, minutes: int) -> int:
        if not (1 <= int(minutes) <= self.max_window_minutes):
            raise PolicyError(f"time window must be 1..{self.max_window_minutes} minutes")
        return int(minutes)

    # ------------------------------------------------------------------ PromQL scoping
    def promql(self, query: str) -> str:
        """PromQL is read-only, but it can read every namespace. Require every
        selector to be pinned to an allowed namespace (or be a node-level metric)."""
        if not query or len(query) > self.max_promql_length:
            raise PolicyError(f"PromQL must be 1..{self.max_promql_length} characters")
        if any(ch in query for ch in ("\x00", "`")):
            raise PolicyError("PromQL contains forbidden characters")

        selectors = list(_SELECTOR.finditer(query))
        spans = [m.span() for m in selectors]
        for m in selectors:
            metric, matchers = m.group(1) or "", m.group(2)
            if metric.startswith(CLUSTER_METRIC_PREFIXES):
                continue
            ns_matchers = _NS_MATCHER.findall(matchers)
            if not ns_matchers:
                raise PolicyError(
                    f"selector {m.group(0)!r} must include namespace=\"<ns>\" "
                    f"(allowed: {', '.join(sorted(self.allowed_namespaces))})")
            for op, value in ns_matchers:
                if op in ("!=", "!~"):
                    raise PolicyError("negative namespace matchers would widen the scope")
                values = value.split("|") if op == "=~" else [value]
                for v in values:
                    if v not in self.allowed_namespaces:
                        raise PolicyError(f"namespace {v!r} in PromQL is outside the investigation scope")

        # bare metric names (no braces), e.g. `up` or `foo[5m]`, are unscoped
        stripped = query
        for a, b in reversed(spans):
            stripped = stripped[:a] + " " * (b - a) + stripped[b:]
        stripped = re.sub(r'"[^"]*"', " ", stripped)
        for tok in re.finditer(r"(?<![\w:.])([a-zA-Z_:][a-zA-Z0-9_:]*)(?![a-zA-Z0-9_:])(?!\s*\()", stripped):
            word = tok.group(1)
            if word in _PROMQL_KEYWORDS or word.startswith(CLUSTER_METRIC_PREFIXES):
                continue
            # durations ("5m") never match this pattern; label names inside by(...) do:
            before = stripped[:tok.start()].rstrip()
            if before.endswith(("by (", "by(", "without (", "without(", ",")) or re.search(
                    r"(by|without|on|ignoring|group_left|group_right)\s*\([^)]*$", stripped[:tok.start()]):
                continue
            raise PolicyError(f"metric {word!r} has no namespace selector; use {word}{{namespace=\"...\"}}")
        return query

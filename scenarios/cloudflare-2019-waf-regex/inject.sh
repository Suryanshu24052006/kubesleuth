#!/usr/bin/env bash
# The rule Cloudflare deployed contained this sub-expression; we keep the full original shape.
set -euo pipefail
kubectl -n "$NS" create configmap edge-waf-rules --dry-run=client -o yaml --from-literal=rules.json='{"rules": [
  {"id": "sqli-union-select", "pattern": "(?i)union\\s+select", "action": "block"},
  {"id": "path-traversal", "pattern": "\\.\\./\\.\\./", "action": "block"},
  {"id": "xss-inline-js-2019-07", "pattern": "(?:(?:\\\"|'"'"'|\\]|\\}|\\\\|\\d|(?:nan|infinity|true|false|null|undefined|symbol|math)|\\`|\\-|\\+)+[)]*;?((?:\\s|-|~|!|{}|\\|\\||\\+)*.*(?:.*=.*)))", "action": "log"}
]}' | kubectl apply -f -
echo "WAF rule pushed (kubelet syncs mounted ConfigMaps within ~60-90 s; edge reloads without restarting)"

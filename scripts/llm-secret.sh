#!/usr/bin/env bash
# Stores whichever LLM API keys are set in your shell as a Secret the agent pod reads.
set -euo pipefail
args=()
for k in ANTHROPIC_API_KEY GOOGLE_API_KEY OPENAI_API_KEY; do
  [ -n "${!k:-}" ] && args+=("--from-literal=$k=${!k}")
done
if [ ${#args[@]} -eq 0 ]; then
  echo "no LLM API key in environment (ANTHROPIC_API_KEY / GOOGLE_API_KEY / OPENAI_API_KEY); in-cluster agent will need one"
  exit 1
fi
kubectl -n kubesleuth create secret generic kubesleuth-llm "${args[@]}" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n kubesleuth rollout restart deploy/kubesleuth-agent >/dev/null 2>&1 || true
echo "secret kubesleuth/kubesleuth-llm updated"

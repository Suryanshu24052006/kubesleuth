# kubesleuth — AI agent for Kubernetes root-cause analysis
SHELL := /bin/bash
PY    ?= .venv/bin/python
S     ?= github-conn-saturation
INCIDENT ?= The checkout service is experiencing a sudden increase in 5xx errors.
MODEL ?= $(or $(KUBESLEUTH_MODEL),anthropic:claude-sonnet-5-5)
REASONER ?= llm

.PHONY: help venv test demo-offline up down images ports scenarios scenario reset investigate \
        investigate-incluster eval eval-rules security-demo security-probe-offline noise-off noise-on fixtures

help:
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

venv: ## local Python env for the CLI, tests and offline demo
	python3 -m venv .venv
	.venv/bin/pip install -q -r broker/requirements.txt -r agent/requirements.txt pytest pyyaml

test: ## unit + protocol + scripted end-to-end tests (no cluster, no API key)
	cd broker && PYTHONPATH=. ../$(PY) -m pytest -q tests
	cd agent && ../$(PY) -m pytest -q tests

fixtures: ## regenerate offline incident snapshots
	$(PY) fixtures/build_fixtures.py

demo-offline: ## run the agent on a recorded incident (REASONER=rules needs no API key)
	PYTHONPATH=agent:broker $(PY) -m kubesleuth_agent investigate "$(INCIDENT)" \
	  --fixture fixtures/github-conn-saturation.json --reasoner $(REASONER) --model $(MODEL) --out reports

security-probe-offline: ## attack the broker policy without a cluster
	PYTHONPATH=agent:broker $(PY) -m kubesleuth_agent.security_probe --fixture fixtures/github-conn-saturation.json

up: ## create kind cluster + install observability, ingress, chaos-mesh, shop, kubesleuth
	./scripts/up.sh

down: ## delete the kind cluster
	./scripts/down.sh

images: ## rebuild images, load into kind, restart
	docker build -q -t shop:1.4.0 --build-arg APP_VERSION=1.4.0 shop/
	docker build -q -t shop:0.9.7 --build-arg APP_VERSION=0.9.7 shop/
	docker build -q -t kubesleuth-broker:0.1.0 broker/
	docker build -q -t kubesleuth-agent:0.1.0 agent/
	kind load docker-image --name kubesleuth shop:1.4.0 shop:0.9.7 kubesleuth-broker:0.1.0 kubesleuth-agent:0.1.0
	kubectl -n kubesleuth rollout restart deploy
	kubectl -n shop rollout restart deploy

ports: ## port-forward Grafana/Prometheus/Alertmanager/Jaeger/broker/agent
	./scripts/ports.sh

scenarios: ## list failure scenarios
	@./scenarios/run.sh list

scenario: ## inject a scenario: make scenario S=<id>
	./scenarios/run.sh $(S) inject

reset: ## restore the healthy baseline
	./scenarios/run.sh reset

investigate: ## run an investigation from your machine via the broker (port-forwarded)
	@kubectl -n kubesleuth port-forward svc/kubesleuth-broker 8090:8090 >/dev/null 2>&1 & PF=$$!; sleep 2; \
	PYTHONPATH=agent $(PY) -m kubesleuth_agent investigate "$(INCIDENT)" --broker http://localhost:8090/mcp \
	  --reasoner $(REASONER) --model $(MODEL) --out reports; kill $$PF

investigate-incluster: ## ask the in-cluster agent (same path Alertmanager uses)
	@kubectl -n kubesleuth port-forward svc/kubesleuth-agent 8081:8080 >/dev/null 2>&1 & PF=$$!; sleep 2; \
	curl -s -XPOST localhost:8081/investigate -H 'content-type: application/json' \
	  -d '{"incident": "$(INCIDENT)"}'; echo; echo "reports: http://localhost:8081 (make ports)"; kill $$PF

eval: ## run all scenarios end to end and score them (LLM reasoner)
	$(PY) eval/run_eval.py --reasoner llm --model $(MODEL)

eval-rules: ## same, with the rule-based baseline
	$(PY) eval/run_eval.py --reasoner rules

security-demo: ## RBAC / credentials / NetworkPolicy / broker-policy checks on the live cluster
	./scripts/security_demo.sh

noise-off: ## stop the adversarial review-bot
	kubectl -n shop scale deploy review-bot --replicas=0

noise-on:
	kubectl -n shop scale deploy review-bot --replicas=1

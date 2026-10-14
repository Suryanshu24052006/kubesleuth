"""The evaluation scorer only credits the agent's actual conclusion (found by reviewing live run 3)."""
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eval"))
from score import score  # noqa: E402

GT = yaml.safe_load((ROOT / "scenarios/github-conn-saturation/scenario.yaml").read_text())["ground_truth"]


def report(statement, component, label="high"):
    return {"root_cause": {"statement": statement, "component": component, "hypothesis": "H1"},
            "confidence": {"label": label, "posterior": 0.9}, "evidence": [], "stats": {}}


def test_victim_story_is_not_correct_even_if_component_field_matches():
    # live run 3: blamed inventory's DB failures; the component field happened to say "checkout"
    r = report("The inventory service is encountering database connection failures, causing 5xx on checkout.",
               "checkout")
    assert score(r, GT)["verdict"] == "partial"


def test_right_cause_with_victim_crowned_is_partial():
    r = report("DB_POOL_SIZE in checkout-config was increased from 4 to 30, exhausting connections.", "inventory")
    assert score(r, GT)["verdict"] == "partial"


def test_full_cause_is_correct():
    r = report("The checkout-config change DB_POOL_SIZE 4 -> 30 exhausted Postgres connections.",
               "configmap/checkout-config")
    assert score(r, GT)["verdict"] == "correct"


def test_mechanism_only_in_causal_chain_does_not_count():
    r = report("The edge proxy is overloaded.", "edge")
    r["causal_chain"] = [{"step": "DB_POOL_SIZE in checkout-config changed", "observation_ids": []}]
    assert score(r, GT)["verdict"] == "wrong"


def test_inconclusive_stays_inconclusive():
    assert score(report("unclear", "unknown", label="inconclusive"), GT)["verdict"] == "inconclusive"

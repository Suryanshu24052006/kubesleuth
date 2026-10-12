from kubesleuth_agent.ledger import Ledger
from kubesleuth_agent.observations import ObservationStore


def setup():
    store = ObservationStore()
    o1 = store.add("search_logs", {}, "", True, '{"source": "loki", "data": {"x": "FATAL:  sorry, too many clients already"}}', 1)
    o2 = store.add("recent_changes", {}, "", True, '{"source": "kubernetes", "data": {"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"}}', 1)
    o3 = store.add("find_traces", {}, "", True, '{"source": "jaeger", "data": {"service": "inventory", "message": "too many clients"}}', 1)
    led = Ledger(store)
    h1 = led.add_hypothesis("checkout-config pool size change exhausted postgres connections", "m", "configmap/checkout-config", "configuration")
    h2 = led.add_hypothesis("inventory has a code defect", "m", "inventory", "code_defect")
    return store, led, h1, h2, (o1, o2, o3)


def test_fabricated_quote_is_rejected():
    _, led, h1, _, (o1, *_ ) = setup()
    ev = led.add_evidence(h1.id, o1.id, "the root cause is DNS failure in kube-dns", "supports", "strong", "made up")
    assert not ev.accepted and "not found" in ev.reject_reason
    assert led.score(h1.id) == 0


def test_quote_matching_tolerates_json_escaping_and_whitespace():
    _, led, h1, _, (o1, o2, _) = setup()
    assert led.add_evidence(h1.id, o1.id, "FATAL: sorry, too many clients already", "supports", "strong", "").accepted
    assert led.add_evidence(h1.id, o2.id, '"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"', "supports", "strong", "").accepted


def test_unknown_observation_or_hypothesis_rejected():
    _, led, h1, _, _ = setup()
    assert not led.add_evidence(h1.id, "O99", "anything at all here", "supports", "strong", "").accepted
    assert not led.add_evidence("H42", "O1", "too many clients already", "supports", "strong", "").accepted


def test_same_observation_counts_once():
    _, led, h1, _, (o1, *_) = setup()
    led.add_evidence(h1.id, o1.id, "too many clients already", "supports", "strong", "")
    dup = led.add_evidence(h1.id, o1.id, "sorry, too many clients", "supports", "strong", "")
    assert not dup.accepted and "duplicate" in dup.reject_reason


def test_multi_source_support_drives_high_confidence_and_competitor_down():
    _, led, h1, h2, (o1, o2, o3) = setup()
    led.add_evidence(h1.id, o1.id, "too many clients already", "supports", "strong", "")
    led.add_evidence(h1.id, o2.id, "data.DB_POOL_SIZE", "supports", "strong", "")
    led.add_evidence(h1.id, o3.id, '"message": "too many clients"', "supports", "moderate", "")
    led.add_evidence(h2.id, o3.id, '"service": "inventory"', "contradicts", "moderate", "victim, not cause")
    label, p, top = led.confidence()
    assert top.id == h1.id and label == "high" and p > 0.9
    assert led.posteriors()[h2.id] < 0.02


def test_single_source_repetition_decays():
    store = ObservationStore()
    obs = [store.add("pod_logs", {"i": i}, "", True, f'{{"source": "kubernetes-logs", "line": "error number {i} boom"}}', 1) for i in range(6)]
    led = Ledger(store)
    h = led.add_hypothesis("x", "m", "c", "other")
    for i, o in enumerate(obs):
        led.add_evidence(h.id, o.id, f"error number {i} boom", "supports", "strong", "")
    # six strong items from ONE source are worth far less than 6 x 2.3
    assert led.score(h.id) < 6
    label, _, _ = led.confidence()
    assert label != "high"  # single source can never be "high"


def test_symptoms_are_never_concluded():
    _, led, _, _, (o1, *_) = setup()
    s = led.add_hypothesis("edge returns 5xx", "m", "edge", "other", layer="symptom")
    led.add_evidence(s.id, o1.id, "too many clients already", "supports", "strong", "")
    assert all(h.layer == "cause" for h, _ in led.ranked())


def test_no_evidence_is_inconclusive():
    _, led, *_ = setup()
    label, p, _ = led.confidence()
    assert label == "inconclusive" and p < 0.35


def test_reproposed_hypothesis_is_merged():
    _, led, h1, *_ = setup()
    again = led.add_hypothesis("checkout-config pool size change exhausted the postgres connections", "m",
                               "configmap/checkout-config", "configuration")
    assert again.id == h1.id and len(led.hypotheses) == 2

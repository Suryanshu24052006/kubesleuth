"""Exercise the real LLMReasoner code path (prompt formatting, structured output parsing,
usage accounting) with a fake LangChain chat model that answers via tool calls, the
same mechanism Anthropic/OpenAI/Gemini structured output uses."""
import asyncio
import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool

from kubesleuth_agent.investigation import Budget, Investigation
from kubesleuth_agent.reasoners import LLMReasoner
from kubesleuth_agent.toolclient import BrokerClient


class FakeToolModel(BaseChatModel):
    answers: dict = {}
    prompts: list = []
    bound: str = ""

    @property
    def _llm_type(self) -> str:
        return "fake-tool-model"

    def bind_tools(self, tools, **kwargs: Any):
        self.bound = convert_to_openai_tool(tools[0])["function"]["name"]
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.prompts.append((self.bound, messages[-1].content))
        queue = self.answers.get(self.bound) or [{}]
        args = queue.pop(0) if len(queue) > 1 else queue[0]
        args = args(messages[-1].content) if callable(args) else args
        msg = AIMessage(content="", tool_calls=[{"name": self.bound, "args": args, "id": "call_1"}],
                        usage_metadata={"input_tokens": 100, "output_tokens": 20, "total_tokens": 120})
        return ChatResult(generations=[ChatGeneration(message=msg)])


def test_llm_reasoner_one_call_per_round(broker):
    def step(prompt: str):
        # behave like a model that read the fenced observations: propose a hypothesis (N1) and
        # cite the config diff verbatim for it in the same answer
        if '"field": "data.DB_POOL_SIZE"' in prompt and "H1 p=" not in prompt:
            oid = prompt.split('tool="recent_changes"')[0].rsplit('<observation id="', 1)[1].split('"')[0]
            return {"new_hypotheses": [{"statement": "pool size change exhausted postgres", "mechanism": "m",
                                        "component": "configmap/checkout-config", "category": "Config",
                                        "layer": "cause"}],
                    "evidence": [{"hypothesis_id": "N1", "observation_id": oid,
                                  "quote": '"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"',
                                  "stance": "supporting", "strength": "strong", "rationale": "the change"}],
                    "next_calls": [{"tool": "find_traces", "args_json": {"service": "edge"}, "purpose": "origin"}]}
        return {"enough_evidence": True}

    fake = FakeToolModel(answers={
        "Step": [step],
        "ReportDraft": [{"root_cause": "rc", "causal_chain": [{"step": "s", "observation_ids": ["O3"]}]}],
    })
    reasoner = LLMReasoner.with_model(fake, "llm:fake")

    async def go():
        async with BrokerClient(broker) as client:
            inv = Investigation("checkout 5xx", "shop", client, reasoner, Budget(max_rounds=3))
            return await inv.run()
    report = asyncio.run(go())

    kinds = [k for k, _ in fake.prompts]
    # one Step call per round (triage + rounds) and one report call; no separate hypothesize/plan calls
    assert set(kinds) == {"Step", "ReportDraft"} and kinds.count("ReportDraft") == 1
    assert 1 <= kinds.count("Step") <= report["stats"]["rounds"] + 1
    step_prompts = [p for k, p in fake.prompts if k == "Step"]
    assert all('trust="untrusted-data"' in p for p in step_prompts)
    assert "workload_metrics(" in step_prompts[0]
    # N1 was mapped to the real hypothesis id and the lenient enums were normalised
    ev = report["evidence"][0]
    assert ev["hypothesis"] == "H1" and ev["stance"] == "supports" and ev["quote"].startswith('"field"')
    assert report["hypotheses"][0]["category"] == "configuration"
    assert report["stats"]["llm_usage"]["calls"] == len(kinds) and report["stats"]["llm_usage"]["input_tokens"] > 0


def test_unusable_model_fails_fast_instead_of_inconclusive(broker):
    import pytest
    from kubesleuth_agent.reasoners import LLMUnavailable

    class Broken(FakeToolModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            raise RuntimeError("Error calling model 'x' (NOT_FOUND): 404 NOT_FOUND. model no longer available")

    reasoner = LLMReasoner.with_model(Broken(), "llm:broken")

    async def go():
        async with BrokerClient(broker) as client:
            return await Investigation("x", "shop", client, reasoner, Budget(max_rounds=3)).run()
    with pytest.raises(BaseException) as info:
        asyncio.run(go())
    exc = info.value
    while isinstance(exc, BaseExceptionGroup):
        exc = exc.exceptions[0]
    assert isinstance(exc, LLMUnavailable) and "NOT_FOUND" in str(exc)

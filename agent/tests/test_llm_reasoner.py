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


def test_llm_reasoner_full_loop(broker):
    def assess(prompt: str):
        # behave like a model that read the fenced observations: quote the diff verbatim
        if '"field": "data.DB_POOL_SIZE"' in prompt:
            oid = prompt.split('tool="recent_changes"')[0].rsplit('<observation id="', 1)[1].split('"')[0]
            return {"evidence": [{"hypothesis_id": "H1", "observation_id": oid,
                                  "quote": '"field": "data.DB_POOL_SIZE", "old": "4", "new": "30"',
                                  "stance": "supports", "strength": "strong", "rationale": "the change"}]}
        return {}

    fake = FakeToolModel(answers={
        "HypothesisUpdate": [{"new_hypotheses": [{"statement": "pool size change exhausted postgres", "mechanism": "m",
                                                  "component": "configmap/checkout-config", "category": "configuration",
                                                  "layer": "cause", "predictions": ["too many clients in logs"]}]}, {}],
        "Plan": [{"calls": [{"tool": "find_traces", "args_json": json.dumps({"service": "edge"}), "purpose": "origin"}],
                  "enough_evidence": False}, {"calls": [], "enough_evidence": True}],
        "Assessment": [assess],
        "ReportDraft": [{"title": "t", "root_cause": "rc", "causal_chain": [{"step": "s", "observation_ids": ["O3"]}]}],
    })
    reasoner = LLMReasoner.__new__(LLMReasoner)
    reasoner.name, reasoner.model, reasoner.usage = "llm:fake", fake, {"calls": 0, "input_tokens": 0, "output_tokens": 0}

    async def go():
        async with BrokerClient(broker) as client:
            inv = Investigation("checkout 5xx", "shop", client, reasoner, Budget(max_rounds=3))
            return await inv.run()
    report = asyncio.run(go())

    kinds = [k for k, _ in fake.prompts]
    assert {"HypothesisUpdate", "Plan", "Assessment", "ReportDraft"} <= set(kinds)
    assess_prompts = [p for k, p in fake.prompts if k == "Assessment"]
    # observations reach the model fenced and labelled untrusted, and the injection is called out
    assert any('trust="untrusted-data"' in p for p in assess_prompts)
    plan_prompt = next(p for k, p in fake.prompts if k == "Plan")
    assert "workload_metrics(" in plan_prompt and "delete" not in plan_prompt.lower().split("tools")[1][:50]
    assert report["evidence"] and report["evidence"][0]["quote"].startswith('"field"')
    assert report["stats"]["llm_usage"]["calls"] >= 5 and report["stats"]["llm_usage"]["input_tokens"] > 0

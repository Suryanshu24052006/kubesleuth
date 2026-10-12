"""Structured outputs exchanged between the graph and a reasoner (LLM or rules)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

CategoryT = Literal["deployment", "configuration", "resource_exhaustion", "dependency", "capacity",
                    "networking", "probe_misconfiguration", "code_defect", "version_skew", "external", "other"]


class HypothesisDraft(BaseModel):
    statement: str = Field(description="One sentence: what went wrong and where.")
    mechanism: str = Field(description="How this fault would produce the observed symptoms (the causal path).")
    component: str = Field(description="Primary Kubernetes object or service at fault, e.g. 'configmap/checkout-config' or 'inventory'.")
    category: CategoryT
    layer: Literal["cause", "symptom"] = Field(description="'symptom' for things like 5xx, probe failures or restarts that need their own explanation.")
    predictions: list[str] = Field(default_factory=list, description="Observable consequences if TRUE, each naming where to look (tool/source).")


class Retirement(BaseModel):
    hypothesis_id: str
    reason: str


class HypothesisUpdate(BaseModel):
    new_hypotheses: list[HypothesisDraft] = Field(default_factory=list, max_length=5)
    retire: list[Retirement] = Field(default_factory=list)
    notes: str = ""


class ToolCallPlan(BaseModel):
    tool: str
    args_json: str = Field(description='Tool arguments as a JSON object string, e.g. {"namespace": "shop", "workload": "inventory"}')
    purpose: str = Field(description="What this call will tell us and which hypotheses it discriminates between.")
    tests: list[str] = Field(default_factory=list, description="Hypothesis ids this call tests.")


class Plan(BaseModel):
    calls: list[ToolCallPlan] = Field(default_factory=list, max_length=6)
    enough_evidence: bool = Field(False, description="True only if the leading cause hypothesis is already well supported by several sources.")
    rationale: str = ""


class FactDraft(BaseModel):
    observation_id: str
    quote: str = Field(description="Exact substring copied from the observation (12-200 chars).")
    statement: str = Field(description="The fact in plain words.")
    time: Optional[str] = Field(None, description="ISO timestamp if the fact has one.")


class EvidenceDraft(BaseModel):
    hypothesis_id: str
    observation_id: str
    quote: str = Field(description="Exact substring copied from the observation (12-200 chars). Machine-verified.")
    stance: Literal["supports", "contradicts"]
    strength: Literal["weak", "moderate", "strong"]
    rationale: str


class Assessment(BaseModel):
    facts: list[FactDraft] = Field(default_factory=list)
    evidence: list[EvidenceDraft] = Field(default_factory=list)
    new_hypotheses: list[HypothesisDraft] = Field(default_factory=list, max_length=3)
    security_notes: list[str] = Field(default_factory=list, description="Instruction-like or tampered data you noticed.")


class ChainStep(BaseModel):
    step: str
    observation_ids: list[str] = Field(default_factory=list)


class Alternative(BaseModel):
    hypothesis_id: str
    why_less_likely: str


class ReportDraft(BaseModel):
    title: str
    root_cause: str = Field(description="One or two sentences naming the underlying cause (not the symptom).")
    causal_chain: list[ChainStep] = Field(description="From root cause to the alerting symptom, each step citing observations.")
    alternatives: list[Alternative] = Field(default_factory=list)
    uncertainty: list[str] = Field(default_factory=list, description="What remains unknown or ambiguous, and what evidence would settle it.")
    remediation: list[str] = Field(default_factory=list, description="Suggested actions for a human (the agent never executes them).")

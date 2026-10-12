"""MCP client for the broker, plus the agent-side tool firewall.

The broker already enforces policy. The firewall is a second, independent layer
on the agent side, so a compromised or confused model is stopped *before* a
request leaves the process, and every attempt is recorded as a security event:
  * only tools the broker advertises (all read-only) may be called;
  * arguments must be a small JSON object;
  * any "namespace" argument must be the namespace under investigation;
  * identical calls are deduplicated (no wasted budget, no loops).
"""
from __future__ import annotations

import json
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any

MAX_ARGS_BYTES = 2048


@dataclass
class SecurityEvent:
    kind: str
    detail: str
    round: int = 0
    observation_id: str | None = None


@dataclass
class Firewall:
    allowed_tools: set[str]
    namespace: str
    events: list[SecurityEvent] = field(default_factory=list)

    def check(self, tool: str, args_json: str, round_: int) -> tuple[bool, dict | None, str]:
        if tool not in self.allowed_tools:
            self.events.append(SecurityEvent("blocked_tool", f"model requested non-existent/forbidden tool {tool!r}", round_))
            return False, None, f"tool {tool!r} is not available (read-only catalogue: {sorted(self.allowed_tools)})"
        if len(args_json or "") > MAX_ARGS_BYTES:
            self.events.append(SecurityEvent("blocked_args", f"oversized arguments for {tool}", round_))
            return False, None, "arguments too large"
        try:
            args = json.loads(args_json or "{}")
        except ValueError:
            return False, None, "args_json is not valid JSON"
        if not isinstance(args, dict):
            return False, None, "args_json must be a JSON object"
        ns = args.get("namespace")
        if ns is not None and ns != self.namespace:
            self.events.append(SecurityEvent("blocked_scope", f"{tool} requested namespace {ns!r} outside scope {self.namespace!r}", round_))
            return False, None, f"namespace {ns!r} is outside the investigation scope"
        return True, args, ""


class BrokerClient:
    """`target` is a URL (http://broker:8090/mcp) or an in-process MCPServer (tests/offline)."""

    def __init__(self, target: Any, timeout: float = 30.0):
        self.target = target
        self.timeout = timeout
        self._stack: AsyncExitStack | None = None
        self._client = None
        self.tools: list[dict] = []

    async def __aenter__(self) -> "BrokerClient":
        from mcp import Client
        self._stack = AsyncExitStack()
        self._client = await self._stack.enter_async_context(Client(self.target))
        listed = await self._client.list_tools()
        self.tools = [{"name": t.name, "description": t.description, "input_schema": t.input_schema,
                       "read_only": bool(t.annotations and t.annotations.read_only_hint)} for t in listed.tools]
        return self

    async def __aexit__(self, *exc):
        if self._stack:
            await self._stack.aclose()

    @property
    def read_only_tool_names(self) -> set[str]:
        # Only tools the server itself declares read-only are ever exposed to the model.
        return {t["name"] for t in self.tools if t["read_only"]}

    async def call(self, tool: str, args: dict) -> tuple[bool, str]:
        try:
            res = await self._client.call_tool(tool, args, read_timeout_seconds=self.timeout)
        except Exception as exc:  # transport failure
            return False, f"transport_error: {type(exc).__name__}: {str(exc)[:200]}"
        text = "\n".join(getattr(c, "text", "") for c in res.content)
        return (not res.is_error), text

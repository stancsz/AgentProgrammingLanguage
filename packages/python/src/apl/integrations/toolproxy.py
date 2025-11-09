"""Minimal ToolProxy adapter definitions for APL.

This module provides:
- ToolProxy: a lightweight protocol describing adapters the runtime can call.
- StorageResult: structured result returned by storage adapters (deterministic, auditable).
- MockStorageProxy: a simple in-memory/mock implementation used for tests and offline runs.

The goal is to centralize side-effect access (storage, network, llm proxies) behind a single adapter
interface so the runtime can:
- check adapter-declared capabilities before performing actions
- emit consistent audit metadata
- swap real adapters for mocks in tests
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any, Dict, Optional, List

@dataclass
class StorageResult:
    status: str
    key: Optional[str] = None
    meta: Dict[str, Any] = None

class ToolProxy(Protocol):
    """Protocol / interface for runtime adapters.

    Implementations declare what capabilities they provide and expose a generic
    perform(tool, args, context) method that returns either a raw result or
    a structured result object.
    """

    def capabilities(self) -> List[str]:
        """Return a list of capability strings this adapter provides (e.g. ['storage'])."""
        ...

    def perform(self, tool: str, args: Dict[str, Any], context: Dict[str, Any]) -> Any:
        """Perform a named tool action and return a result.

        - tool: short name of the tool/action, e.g. 'store'
        - args: parsed keyword args for the action
        - context: execution context (task, agent, program meta) for auditing
        """
        ...

class MockStorageProxy:
    """A deterministic, side-effect-free storage proxy used for testing.

    Instead of writing to disk/network this proxy returns structured metadata so
    runtime logic and tests can assert on behaviour without performing IO.
    """

    def __init__(self, base_path: str = "/tmp/apl_storage") -> None:
        self.base_path = base_path

    def capabilities(self) -> List[str]:
        return ["storage"]

    def perform(self, tool: str, args: Dict[str, Any], context: Dict[str, Any]) -> StorageResult:
        if tool != "store":
            raise RuntimeError(f"MockStorageProxy only supports 'store' tool, got '{tool}'")
        key = args.get("key") or args.get("path") or "item"
        content = args.get("content") or args.get("value") or ""
        meta = {
            "requesting_task": context.get("task"),
            "agent": context.get("agent"),
            "key": key,
            "size": len(str(content)),
            "base_path": self.base_path,
        }
        return StorageResult(status="ok", key=key, meta=meta)

__all__ = ["ToolProxy", "StorageResult", "MockStorageProxy"]

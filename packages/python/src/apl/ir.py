"""IR serializers for APL programs."""

from __future__ import annotations

import uuid
from typing import Any, Dict

from .ast import Program


def to_langgraph_ir(program: Program) -> Dict[str, Any]:
    """Serialize to a LangGraph-inspired JSON structure (prototype)."""
    nodes = []
    edges = []
    for task in program.tasks:
        prev_id = None
        for step in task.steps:
            node_id = str(uuid.uuid4())
            nodes.append(
                {
                    "id": node_id,
                    "task": task.name,
                    "kind": step.action or "call_llm",
                    "input": step.args,
                    "assignment": step.assignment,
                    "requires": step.requires,
                    "source": step.raw,
                }
            )
            if prev_id:
                edges.append([prev_id, node_id])
            prev_id = node_id
    return {
        "program": program.name,
        "meta": program.meta,
        "nodes": nodes,
        "edges": edges,
    }


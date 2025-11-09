"""IR serializers for APL programs with deterministic IDs and provenance."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .ast import Program

# TODO: IR SCHEMA & PROVENANCE VALIDATION
# - Define a JSON Schema or pydantic models describing the IR payload structure
#   (program, meta, generator, schema_version, nodes, edges, ir_hash).
# - Validate the IR in to_langgraph_ir() and in the CLI compile step to fail fast on
#   schema drift. Emit clear diagnostic messages showing which field(s) are invalid.
# - Consider publishing the schema as docs/apl-spec/ir-schema.json and reusing it
#   in CI for schema validation tests.
# - Ensure ir_hash covers canonicalized nodes+edges+generator and document the
#   provenance rules in DESIGN_PRINCIPLES.md and README.md.

# Keep a stable generator identifier in sync with setup.py version
_GENERATOR = "apl/0.1.0"
_SCHEMA_VERSION = "1.0"


def _deterministic_node_id(program_name: str, task_name: str, index: int, step_source: str) -> str:
    """Create a stable node id from program/task/index/source and generator."""
    m = hashlib.sha256()
    m.update(_GENERATOR.encode("utf-8"))
    m.update(b"|")
    m.update(program_name.encode("utf-8"))
    m.update(b"|")
    m.update(task_name.encode("utf-8"))
    m.update(b"|")
    m.update(str(index).encode("utf-8"))
    m.update(b"|")
    m.update(step_source.encode("utf-8"))
    return m.hexdigest()


def _compute_ir_hash(payload: Dict[str, Any]) -> str:
    """Compute a deterministic hash for the IR payload."""
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def to_langgraph_ir(program: Program) -> Dict[str, Any]:
    """Serialize to a LangGraph-inspired JSON structure (deterministic where possible)."""
    nodes: List[Dict[str, Any]] = []
    edges: List[List[str]] = []

    for t_idx, task in enumerate(program.tasks):
        prev_id: str | None = None
        for s_idx, step in enumerate(task.steps):
            node_id = _deterministic_node_id(program.name, task.name, s_idx, step.raw)
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

    payload = {
        "program": program.name,
        "meta": program.meta,
        "generator": _GENERATOR,
        "schema_version": _SCHEMA_VERSION,
        "nodes": nodes,
        "edges": edges,
    }

    # attach an IR-level hash for provenance/audit
    payload["ir_hash"] = _compute_ir_hash({"nodes": payload["nodes"], "edges": payload["edges"], "generator": payload["generator"]})

    return payload

"""High-level author -> compile -> adapt -> validate pipeline helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any

from .authoring import LiteLLMAuthor, AuthoringConfig
from .parser import parse_apl
from .compiler import write_compiled_artifacts
from .ir import to_langgraph_ir
from .n8n import to_n8n_workflow
from .runtime import Runtime


@dataclass
class PipelineArtifacts:
    """Paths to artifacts produced by the end-to-end pipeline."""

    prompt_path: Path
    apl_path: Path
    python_path: Path
    ir_path: Path
    n8n_path: Path
    run_path: Path
    outputs: Dict[str, Any]


def run_pipeline(
    prompt: str,
    out_dir: Path,
    name: str = "demo_program",
    *,
    allow_storage: bool = False,
    author_config: Optional[AuthoringConfig] = None,
    seed_vars: Optional[Dict[str, Any]] = None,
) -> PipelineArtifacts:
    """Execute the 4-step pipeline and persist artifacts to disk."""
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = out_dir / f"{name}_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    author = LiteLLMAuthor(author_config)
    apl_source = author.generate_program(prompt)

    apl_path = out_dir / f"{name}.apl"
    apl_path.write_text(apl_source, encoding="utf-8")

    program = parse_apl(apl_source)

    python_path = out_dir / f"{name}.py"
    ir_path = out_dir / f"{name}.json"
    write_compiled_artifacts(program, python_out=python_path, ir_path=ir_path)

    try:
        workflow = to_n8n_workflow(program)
    except ValueError as exc:
        workflow = {
            "name": name,
            "warning": str(exc),
            "nodes": [],
            "connections": {},
        }
    n8n_path = out_dir / f"{name}_n8n.json"
    n8n_path.write_text(json.dumps(workflow, indent=2), encoding="utf-8")

    runtime = Runtime(allow_storage=allow_storage)
    if seed_vars:
        runtime.vars.update(seed_vars)
    for task in program.tasks:
        for arg in task.args:
            runtime.vars.setdefault(arg, None)

    try:
        outputs = runtime.execute_program(program)
    except Exception as exc:
        outputs = {"error": str(exc)}

    run_path = out_dir / f"{name}_run.json"
    run_path.write_text(json.dumps(outputs, indent=2), encoding="utf-8")

    return PipelineArtifacts(
        prompt_path=prompt_path,
        apl_path=apl_path,
        python_path=python_path,
        ir_path=ir_path,
        n8n_path=n8n_path,
        run_path=run_path,
        outputs=outputs,
    )


__all__ = ["run_pipeline", "PipelineArtifacts"]

"""Compilation helpers for converting APL programs into deployable artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import indent
from typing import Optional

from .ast import Program, Task, Step
from .ir import to_langgraph_ir

# TODO: IR SCHEMA VALIDATION & DIAGNOSTICS
# - Validate the IR produced by to_langgraph_ir() against a canonical schema (JSON Schema or pydantic model)
#   before writing files. Fail fast with clear diagnostics indicating which fields are invalid.
# - Emit ir_version and ir_hash in compiled artifacts and surface schema validation warnings/errors in the CLI.
# - Consider adding a --strict flag to the compile command to enforce schema validation in CI/release builds.
# - Implement unit tests that assert invalid IR payloads are rejected and that provenance (ir_hash) is stable.
#
# Notes:
# - This TODO aligns with DESIGN_PRINCIPLES.md ("IR schema & validation") and should be implemented
#   as part of the recommended IR pydantic models PR.
# - Place validation logic near write_compiled_artifacts so the compile pipeline can stop on schema drift.


def _format_step(step: Step) -> str:
    return (
        "Step(\n"
        f"    raw={step.raw!r},\n"
        f"    assignment={step.assignment!r},\n"
        f"    action={step.action!r},\n"
        f"    args={step.args!r},\n"
        f"    requires={step.requires!r},\n"
        ")"
    )


def _format_task(task: Task) -> str:
    steps_repr = ",\n".join(indent(_format_step(step), "        ") for step in task.steps)
    return (
        "Task(\n"
        f"    name={task.name!r},\n"
        f"    args={task.args!r},\n"
        f"    precondition={task.precondition!r},\n"
        f"    postcondition={task.postcondition!r},\n"
        f"    steps=[\n{steps_repr}\n    ],\n"
        ")"
    )


def compile_to_python_module(program: Program) -> str:
    """Emit a Python module that reconstructs the program and exposes run()."""
    tasks_payload = ",\n".join(indent(_format_task(task), "    ") for task in program.tasks)
    return f'''"""Compiled APL program (auto-generated)."""

from apl.ast import Program, Task, Step
from apl.runtime import Runtime

PROGRAM = Program(
    name={program.name!r},
    meta={program.meta!r},
    tasks=[
{tasks_payload}
    ],
)


def run(runtime: Runtime | None = None):
    runtime = runtime or Runtime()
    return runtime.execute_program(PROGRAM)
'''


def write_compiled_artifacts(
    program: Program,
    python_out: Optional[Path] = None,
    ir_path: Optional[Path] = None,
) -> None:
    """Write compiled artifacts (Python module, IR JSON) to the filesystem."""
    if python_out:
        python_out.parent.mkdir(parents=True, exist_ok=True)
        python_out.write_text(compile_to_python_module(program), encoding="utf-8")
    if ir_path:
        ir_path.parent.mkdir(parents=True, exist_ok=True)
        ir_path.write_text(json.dumps(to_langgraph_ir(program), indent=2), encoding="utf-8")

"""Compilation helpers for converting APL programs into deployable artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import indent
from typing import Optional

from .ast import Program, Task, Step
from .ir import to_langgraph_ir, _validate_ir


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
    python_path: Optional[Path] = None,
) -> None:
    """Write compiled artifacts (Python module, IR JSON) to the filesystem.

    Backwards-compatible parameter aliases:
    - python_path is accepted as an alias for python_out to match older tests.
    This function validates the produced IR against the canonical pydantic model
    and fails fast if validation errors are detected.
    """
    # support legacy alias used by tests
    if python_path and not python_out:
        python_out = python_path

    if python_out:
        python_out.parent.mkdir(parents=True, exist_ok=True)
        python_out.write_text(compile_to_python_module(program), encoding="utf-8")
    if ir_path:
        ir_path.parent.mkdir(parents=True, exist_ok=True)
        payload = to_langgraph_ir(program)
        # validate IR schema before writing to disk
        _validate_ir(payload)
        ir_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

"""Command line interface for the Agent Programming Language (APL)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .parser import parse_apl
from .runtime import Runtime
from .ir import to_langgraph_ir
from .compiler import write_compiled_artifacts


def _load_program(path: Path):
    text = path.read_text(encoding="utf-8")
    return parse_apl(text)


def _cmd_validate(path: Path) -> None:
    program = _load_program(path)
    summary = {
        "program": program.name,
        "meta": program.meta,
        "tasks": [
            {
                "name": task.name,
                "args": task.args,
                "steps": [step.raw for step in task.steps],
            }
            for task in program.tasks
        ],
    }
    print(json.dumps(summary, indent=2))


def _cmd_translate(path: Path) -> None:
    program = _load_program(path)
    print(json.dumps(to_langgraph_ir(program), indent=2))


def _cmd_run(path: Path, allow_storage: bool) -> None:
    program = _load_program(path)
    runtime = Runtime(allow_storage=allow_storage)
    result = runtime.execute_program(program)
    print(json.dumps(result, indent=2))


def _cmd_compile(path: Path, python_out: Path | None, ir_out: Path | None) -> None:
    program = _load_program(path)
    if not python_out and not ir_out:
        raise SystemExit("compile requires at least one of --python-out or --ir-out")
    write_compiled_artifacts(program, python_out=python_out, ir_path=ir_out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="apl", description="Agent Programming Language CLI")
    sub = parser.add_subparsers(dest="command")

    p_val = sub.add_parser("validate", help="Parse and display a summary of the program")
    p_val.add_argument("file", type=Path)

    p_trans = sub.add_parser("translate", help="Emit LangGraph-like IR")
    p_trans.add_argument("file", type=Path)

    p_run = sub.add_parser("run", help="Execute the program with the reference runtime")
    p_run.add_argument("file", type=Path)
    p_run.add_argument("--allow-storage", action="store_true", help="Enable storage capability during execution")

    p_comp = sub.add_parser("compile", help="Compile program to artifacts (Python module / IR)")
    p_comp.add_argument("file", type=Path)
    p_comp.add_argument("--python-out", type=Path, help="Path to write compiled Python module")
    p_comp.add_argument("--ir-out", type=Path, help="Path to write IR JSON")

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        _cmd_validate(args.file)
    elif args.command == "translate":
        _cmd_translate(args.file)
    elif args.command == "run":
        _cmd_run(args.file, allow_storage=args.allow_storage)
    elif args.command == "compile":
        _cmd_compile(args.file, python_out=args.python_out, ir_out=args.ir_out)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()

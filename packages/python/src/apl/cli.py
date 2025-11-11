"""Command line interface for the Agent Programming Language (APL)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .env import load_env_defaults
from .parser import parse_apl
from .runtime import Runtime
from .compiler import write_compiled_artifacts
from .n8n import to_n8n_workflow
from .ir import _validate_ir, to_langgraph_ir
from .authoring import LiteLLMAuthor, AuthoringConfig
from .pipeline import run_pipeline


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


def _cmd_translate(path: Path, strict: bool = False) -> None:
    program = _load_program(path)
    payload = to_langgraph_ir(program)
    # validate IR before emitting to surface schema issues early
    try:
        _validate_ir(payload)
    except Exception as e:
        if strict:
            raise SystemExit(f"IR validation failed: {e}")
        else:
            print(f"IR validation warning: {e}")
    print(json.dumps(payload, indent=2))


def _cmd_run(path: Path, allow_storage: bool, strict: bool = False) -> None:
    program = _load_program(path)

    # CLI preflight: ensure declared capabilities match step requirements.
    agents_meta = program.meta.get("agents", {})
    missing = []
    for task in program.tasks:
        # task names are typically "agent.fn"; fall back safely
        agent_name = task.name.split(".", 1)[0] if "." in task.name else None
        declared_caps = []
        if agent_name and agent_name in agents_meta:
            declared_caps = agents_meta[agent_name].get("capabilities", [])
        for step in task.steps:
            for req in step.requires:
                # allow runtime override for storage capability via --allow-storage
                if req == "storage" and allow_storage:
                    continue
                if req not in declared_caps:
                    missing.append((task.name, step.raw, req))
    if missing:
        msg_lines = [f"Missing required capability '{req}' for task '{task_name}' at step: {raw}" for task_name, raw, req in missing]
        full = "\n".join(msg_lines)
        if strict:
            raise SystemExit(f"Preflight capability check failed:\n{full}")
        else:
            print(f"Preflight capability warnings:\n{full}")

    runtime = Runtime(allow_storage=allow_storage)
    result = runtime.execute_program(program)
    print(json.dumps(result, indent=2))


def _cmd_compile(path: Path, python_out: Path | None, ir_out: Path | None, strict: bool = False) -> None:
    program = _load_program(path)
    if not python_out and not ir_out:
        raise SystemExit("compile requires at least one of --python-out or --ir-out")
    # validate IR early to provide clearer compile-time diagnostics
    if ir_out:
        payload = to_langgraph_ir(program)
        try:
            _validate_ir(payload)
        except Exception as e:
            if strict:
                raise SystemExit(f"IR validation failed during compile: {e}")
            else:
                print(f"IR validation warning during compile: {e}")
    write_compiled_artifacts(program, python_out=python_out, ir_path=ir_out)


def _cmd_export_n8n(path: Path, runtime_url: str | None, out: Path | None) -> None:
    program = _load_program(path)
    workflow = to_n8n_workflow(program, runtime_url=runtime_url)
    payload = json.dumps(workflow, indent=2)
    if out:
        out.write_text(payload, encoding="utf-8")
    else:
        print(payload)


def _cmd_author(prompt_path: Path, out_path: Path, model: str | None, mock: bool) -> None:
    config = AuthoringConfig(model=model, mock=mock)
    author = LiteLLMAuthor(config)
    prompt = prompt_path.read_text(encoding="utf-8")
    apl_source = author.generate_program(prompt)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(apl_source, encoding="utf-8")
    print(f"Wrote APL program to {out_path}")


def _cmd_demo(
    prompt_path: Path,
    out_dir: Path,
    name: str,
    model: str | None,
    mock_llm: bool,
    allow_storage: bool,
) -> None:
    config = AuthoringConfig(model=model, mock=mock_llm)
    prompt = prompt_path.read_text(encoding="utf-8")
    artifacts = run_pipeline(
        prompt,
        out_dir,
        name=name,
        allow_storage=allow_storage,
        author_config=config,
    )
    summary = {
        "prompt": str(artifacts.prompt_path),
        "apl": str(artifacts.apl_path),
        "python": str(artifacts.python_path),
        "ir": str(artifacts.ir_path),
        "n8n": str(artifacts.n8n_path),
        "run": str(artifacts.run_path),
        "outputs": artifacts.outputs,
    }
    print(json.dumps(summary, indent=2))

def _cmd_repl(path: Path | None) -> None:
    """
    Minimal REPL for iterating on APL programs.

    Usage:
      apl repl                # start empty REPL
      apl repl examples/foo.apl
    Commands:
      run            - execute the loaded program (full run)
      exit, quit     - exit REPL
      help           - show this help
    """
    program = None
    if path:
        try:
            program = _load_program(path)
            print(f"Loaded program: {program.name}")
        except Exception as e:
            print(f"Failed to load program: {e}")
            program = None

    runtime = Runtime()

    print("APL REPL - type 'help' for commands, 'exit' to quit.")
    while True:
        try:
            line = input("apl> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break

        if not line:
            continue
        if line in ("exit", "quit"):
            break
        if line == "help":
            print("Commands: run, help, exit")
            continue

        if line == "run":
            if program is None:
                print("No program loaded. Provide a file path to 'apl repl <file>' to load a program.")
                continue
            try:
                result = runtime.execute_program(program)
                print(json.dumps(result, indent=2))
            except Exception as e:
                print(f"Execution error: {e}")
            continue

        print("Unknown command. Type 'help' for assistance.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="apl", description="Agent Programming Language CLI")
    sub = parser.add_subparsers(dest="command")

    p_val = sub.add_parser("validate", help="Parse and display a summary of the program")
    p_val.add_argument("file", type=Path)

    p_trans = sub.add_parser("translate", help="Emit LangGraph-like IR")
    p_trans.add_argument("file", type=Path)
    p_trans.add_argument("--strict", action="store_true", help="Fail on IR validation warnings")

    p_run = sub.add_parser("run", help="Execute the program with the reference runtime")
    p_run.add_argument("file", type=Path)
    p_run.add_argument("--allow-storage", action="store_true", help="Enable storage capability during execution")
    p_run.add_argument("--strict", action="store_true", help="Treat preflight warnings as errors")

    p_comp = sub.add_parser("compile", help="Compile program to artifacts (Python module / IR)")
    p_comp.add_argument("file", type=Path)
    p_comp.add_argument("--python-out", type=Path, help="Path to write compiled Python module")
    p_comp.add_argument("--ir-out", type=Path, help="Path to write IR JSON")
    p_comp.add_argument("--strict", action="store_true", help="Fail the compile if IR validation reports problems")

    p_repl = sub.add_parser("repl", help="Start a minimal interactive REPL optionally loading a program")
    p_repl.add_argument("file", type=Path, nargs="?", help="Optional APL file to load")

    p_n8n = sub.add_parser("export-n8n", help="Generate an n8n workflow JSON from annotated tasks")
    p_n8n.add_argument("file", type=Path)
    p_n8n.add_argument("--runtime-url", type=str, help="Override the runtime URL used inside the generated workflow")
    p_n8n.add_argument("--out", type=Path, help="Path to write the workflow JSON (stdout if omitted)")

    p_author = sub.add_parser("author", help="Generate an APL program using LiteLLM")
    p_author.add_argument("prompt", type=Path, help="Path to the natural language prompt file")
    p_author.add_argument("--out", type=Path, required=True, help="Output path for the generated APL file")
    p_author.add_argument("--model", type=str, help="Override the LiteLLM model to use")
    p_author.add_argument("--mock", action="store_true", help="Use deterministic mock authoring output")

    p_demo = sub.add_parser("demo", help="Run the 4-step author -> compile -> adapt -> validate pipeline")
    p_demo.add_argument("prompt", type=Path, help="Path to the natural language prompt file")
    p_demo.add_argument("--out-dir", type=Path, default=Path("demo"), help="Directory to write pipeline artifacts")
    p_demo.add_argument("--name", type=str, default="demo_program", help="Base name for generated artifacts")
    p_demo.add_argument("--model", type=str, help="Override the LiteLLM model to use")
    p_demo.add_argument("--mock-llm", action="store_true", help="Use deterministic mock authoring output")
    p_demo.add_argument("--allow-storage", action="store_true", help="Enable storage capability during runtime execution")

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    load_env_defaults()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate":
        _cmd_validate(args.file)
    elif args.command == "translate":
        _cmd_translate(args.file, strict=getattr(args, "strict", False))
    elif args.command == "run":
        _cmd_run(args.file, allow_storage=args.allow_storage, strict=getattr(args, "strict", False))
    elif args.command == "compile":
        _cmd_compile(args.file, python_out=args.python_out, ir_out=args.ir_out, strict=getattr(args, "strict", False))
    elif args.command == "repl":
        _cmd_repl(getattr(args, "file", None))
    elif args.command == "export-n8n":
        _cmd_export_n8n(args.file, runtime_url=getattr(args, "runtime_url", None), out=getattr(args, "out", None))
    elif args.command == "author":
        _cmd_author(args.prompt, args.out, getattr(args, "model", None), mock=getattr(args, "mock", False))
    elif args.command == "demo":
        _cmd_demo(
            args.prompt,
            getattr(args, "out_dir", Path("demo")),
            getattr(args, "name", "demo_program"),
            getattr(args, "model", None),
            getattr(args, "mock_llm", False),
            getattr(args, "allow_storage", False),
        )
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()

import importlib.util
import json
import sys
from pathlib import Path

import pytest


# Ensure the apl package under packages/python/src is importable when tests run in repo root.
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "packages" / "python" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apl.parser import parse_apl  # noqa: E402  (import after sys.path tweak)
from apl.runtime import Runtime  # noqa: E402
from apl.compiler import write_compiled_artifacts  # noqa: E402
from apl.ir import to_langgraph_ir  # noqa: E402


EXAMPLE = ROOT / "examples" / "hello.apl"


def test_parse_and_run_example():
    program = parse_apl(EXAMPLE.read_text(encoding="utf-8"))
    assert program.tasks, "Parser should discover tasks"
    assert any(t.name == "hello_world.greet" for t in program.tasks)

    runtime = Runtime()
    result = runtime.execute_program(program)
    assert "hello_world.greet" in result
    assert any("mocked" in str(v) for v in result["hello_world.greet"].values())


def test_langgraph_ir_generation():
    program = parse_apl(EXAMPLE.read_text(encoding="utf-8"))
    ir = to_langgraph_ir(program)
    assert ir["program"] == program.name or ir["program"] == "__unnamed__"
    assert ir["nodes"], "IR should contain nodes"
    # Ensure edges connect nodes sequentially
    node_ids = {node["id"] for node in ir["nodes"]}
    for edge in ir["edges"]:
        assert edge[0] in node_ids and edge[1] in node_ids


def test_compile_to_python_module(tmp_path: Path):
    program = parse_apl(EXAMPLE.read_text(encoding="utf-8"))
    python_path = tmp_path / "compiled_agent.py"
    ir_path = tmp_path / "compiled_agent.json"

    write_compiled_artifacts(program, python_path=python_path, ir_path=ir_path)
    assert python_path.exists()
    assert ir_path.exists()

    compiled = json.loads(ir_path.read_text(encoding="utf-8"))
    assert compiled["nodes"], "IR artifact should contain nodes"

    spec = importlib.util.spec_from_file_location("compiled_agent", python_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[attr-defined]

    output = module.run()
    assert isinstance(output, dict)
    assert "hello_world.greet" in output

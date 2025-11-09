import pytest
from pathlib import Path

import apl.cli as cli
from apl.ast import Program, Task, Step

def _make_program_requires_storage(agent_name: str = "agent") -> Program:
    return Program(
        name="p",
        meta={},  # no agent capabilities declared
        tasks=[
            Task(
                name=f"{agent_name}.save",
                args=[],
                steps=[
                    Step(
                        raw='store key="x", content="y"',
                        assignment="out",
                        action="store",
                        args='key="x", content="y"',
                        requires=["storage"],
                    )
                ],
            )
        ],
    )

def test_cmd_run_preflight_warns_and_runtime_error(monkeypatch):
    """Non-strict preflight should print warnings but runtime execution will still error
    due to missing capability (tested via Runtime raising)."""
    prog = _make_program_requires_storage("agent1")
    monkeypatch.setattr(cli, "_load_program", lambda path: prog)

    # allow_storage not set, strict=False -> preflight prints warnings then runtime.execute_program raises
    with pytest.raises(RuntimeError):
        cli._cmd_run(Path("dummy.apl"), allow_storage=False, strict=False)

def test_cmd_run_preflight_strict_fails_early(monkeypatch):
    """Strict preflight should exit with SystemExit before attempting runtime execution."""
    prog = _make_program_requires_storage("agent1")
    monkeypatch.setattr(cli, "_load_program", lambda path: prog)

    with pytest.raises(SystemExit):
        cli._cmd_run(Path("dummy.apl"), allow_storage=False, strict=True)

def test_cmd_translate_strict_and_warns(monkeypatch, capsys):
    """If IR validation raises, strict mode should SystemExit; non-strict should emit a warning."""
    # prepare a minimal program and a dummy payload
    prog = Program(name="p", meta={}, tasks=[])
    monkeypatch.setattr(cli, "_load_program", lambda path: prog)

    # monkeypatch _validate_ir to raise
    def _raise_validate(payload):
        raise Exception("broken IR")
    monkeypatch.setattr(cli, "_validate_ir", _raise_validate)

    # strict=True -> should SystemExit
    with pytest.raises(SystemExit):
        cli._cmd_translate(Path("dummy.apl"), strict=True)

    # strict=False -> should print a warning and still print payload
    cli._cmd_translate(Path("dummy.apl"), strict=False)
    captured = capsys.readouterr()
    assert "IR validation warning" in captured.out or "broken IR" in captured.out

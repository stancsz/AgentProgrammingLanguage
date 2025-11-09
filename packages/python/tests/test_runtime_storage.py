import pytest

from apl.runtime import Runtime
from apl.ast import Program, Task, Step
from apl.integrations.toolproxy import MockStorageProxy

def test_store_with_tool_proxy():
    program = Program(
        name="p",
        meta={
            "agents": {
                "agent1": {"capabilities": ["storage"]}
            }
        },
        tasks=[
            Task(
                name="agent1.save",
                args=[],
                steps=[
                    Step(
                        raw='store key="file1", content="hello"',
                        assignment="out",
                        action="store",
                        args='key="file1", content="hello"',
                        requires=["storage"],
                    )
                ],
            )
        ],
    )

    runtime = Runtime(tool_proxy=MockStorageProxy())
    results = runtime.execute_program(program)

    assert "agent1.save" in results
    assert results["agent1.save"]["out"]["status"] == "ok"
    assert results["agent1.save"]["out"]["key"] == "file1"
    assert "requesting_task" in results["agent1.save"]["out"]["meta"]

def test_store_with_allow_storage_fallback():
    program = Program(
        name="p",
        meta={},
        tasks=[
            Task(
                name="anon.save",
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

    runtime = Runtime(allow_storage=True)
    results = runtime.execute_program(program)

    assert results["anon.save"]["out"]["status"] == "ok"
    assert results["anon.save"]["out"]["meta"].get("mock") is True

def test_missing_storage_raises():
    program = Program(
        name="p",
        meta={},
        tasks=[
            Task(
                name="agent.save",
                args=[],
                steps=[
                    Step(
                        raw='store key="x"',
                        assignment=None,
                        action="store",
                        args='key="x"',
                        requires=["storage"],
                    )
                ],
            )
        ],
    )

    runtime = Runtime()
    with pytest.raises(RuntimeError):
        runtime.execute_program(program)

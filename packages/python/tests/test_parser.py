import json
from pathlib import Path

# Ensure tests import the local package when run from repo root
import sys
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "packages" / "python" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apl.parser import parse_apl  # noqa: E402

SAMPLE_PROGRAM = """
program demo(version="0.1")

agent notifier(api_key) binds mcp.slack as slack, mcp.storage as s3:
  def run(payload):
    precondition: payload != ""
    step text = "Notify: {{payload}}"
    step sent = slack.post_message(channel="#ops", text=text) requires capability.network
    # n8n: trigger webhook path="/apl/notifier" method="POST"
  end
end
"""

def test_program_header_and_meta():
    prog = parse_apl(SAMPLE_PROGRAM)
    assert prog.name == "demo"
    assert prog.meta.get("version") == "0.1"

def test_agent_and_binds_parsed():
    prog = parse_apl(SAMPLE_PROGRAM)
    agents = prog.meta.get("agents", {})
    assert "notifier" in agents
    binds = agents["notifier"]["binds"]
    assert binds["slack"] == "mcp.slack"
    assert binds["s3"] == "mcp.storage"
    assert agents["notifier"]["args"] == ["api_key"]

def test_def_to_task_and_precondition():
    prog = parse_apl(SAMPLE_PROGRAM)
    task_names = [t.name for t in prog.tasks]
    assert "notifier.run" in task_names
    task = next(t for t in prog.tasks if t.name == "notifier.run")
    assert task.precondition == 'payload != ""'

def test_steps_and_requires_capability():
    prog = parse_apl(SAMPLE_PROGRAM)
    task = next(t for t in prog.tasks if t.name == "notifier.run")
    # find the step that assigns 'sent'
    sent_steps = [s for s in task.steps if s.assignment == "sent"]
    assert sent_steps, "expected a step assigning to 'sent'"
    step = sent_steps[0]
    assert step.action.endswith("post_message") or "post_message" in (step.action or "")
    assert "network" in step.requires

def test_n8n_comment_parsed_into_metadata():
    prog = parse_apl(SAMPLE_PROGRAM)
    task = next(t for t in prog.tasks if t.name == "notifier.run")
    meta = task.metadata
    assert "n8n" in meta
    assert "trigger" in meta["n8n"]
    trigger = meta["n8n"]["trigger"]
    assert trigger["type"] == "webhook"
    assert trigger["config"]["path"] == "/apl/notifier"
    assert trigger["config"]["method"] == "POST"

def test_string_fallback_prompt_handling():
    sample = """
agent a:
  def ask():
    "Hello, how are you?"
  end
end
"""
    prog = parse_apl(sample)
    task = next(t for t in prog.tasks if t.name == "a.ask")
    assert any(s.action == "call_llm" for s in task.steps)
    prompts = [s.args for s in task.steps if s.action == "call_llm"]
    assert any("Hello, how are you?" in p for p in prompts)

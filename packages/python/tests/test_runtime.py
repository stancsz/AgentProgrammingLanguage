import json
from pathlib import Path
import sys

import pytest

# Ensure tests import the local package when run from repo root
ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "packages" / "python" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from apl.parser import parse_apl  # noqa: E402
from apl.runtime import Runtime  # noqa: E402

def test_storage_capability_enforced():
    sample = '''
agent a:
  def s():
    step store("local://data/x.txt", "payload") requires capability.storage
  end
end
'''
    prog = parse_apl(sample)
    runtime = Runtime(allow_storage=False)
    with pytest.raises(RuntimeError) as exc:
        runtime.execute_program(prog)
    assert "Storage capability not enabled" in str(exc.value)

    runtime_ok = Runtime(allow_storage=True)
    result = runtime_ok.execute_program(prog)
    # stored result should appear (runtime returns "stored" for store)
    assert any("s" in vars_snapshot for vars_snapshot in result.values())

def test_precondition_blocks_execution():
    sample = '''
agent a:
  def t():
    precondition: 1 == 0
    step "should not run"
  end
end
'''
    prog = parse_apl(sample)
    runtime = Runtime()
    with pytest.raises(RuntimeError) as exc:
        runtime.execute_program(prog)
    assert "Precondition failed" in str(exc.value)

def test_n8n_requires_client_and_calls_trigger():
    sample = '''
agent a:
  def t():
    step n8n.trigger_webhook(path="/apl/test", method="POST") 
  end
end
'''
    prog = parse_apl(sample)
    runtime = Runtime()
    # without n8n_client configured, runtime should raise
    with pytest.raises(RuntimeError) as exc:
        runtime.execute_program(prog)
    assert "n8n action" in str(exc.value)

    # provide a minimal mock client with the expected method
    class MockClient:
        def trigger_webhook(self, path, payload=None, method="POST"):
            return {"ok": True, "path": path, "method": method}

        def call_workflow(self, workflow_id, payload=None):
            return {"ok": True, "workflow_id": workflow_id}

    runtime_with_client = Runtime(n8n_client=MockClient())
    res = runtime_with_client.execute_program(prog)
    # Should not raise and should include results
    assert isinstance(res, dict)
    # the n8n call result may be present in vars snapshot
    assert any(isinstance(v, dict) or (isinstance(v, str) and "ok" in v) for v in next(iter(res.values())).values())

def test_slack_actions_raise_informative_error():
    sample = '''
agent a:
  def t():
    step slack.post_message(channel="#ops", text="hi")
  end
end
'''
    prog = parse_apl(sample)
    runtime = Runtime()
    with pytest.raises(RuntimeError) as exc:
        runtime.execute_program(prog)
    assert "Slack actions are no longer bundled" in str(exc.value)

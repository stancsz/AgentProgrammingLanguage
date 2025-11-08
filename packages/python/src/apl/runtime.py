"""Runtime interpreter for executing APL programs."""

from __future__ import annotations

import json
import re
from typing import Dict, Any, Optional, TYPE_CHECKING

from .ast import Program, Step

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .n8n import N8NClient


class MockLLM:
    """Deterministic mock LLM used for testing and offline execution."""

    def __init__(self, seed: str = "mock"):
        self.seed = seed

    def call(self, prompt: str, model: str = "mock") -> str:
        prompt = prompt.strip()
        return f"[mocked:{model}] {prompt}"


class Runtime:
    """Reference runtime that interprets an APL Program."""

    def __init__(self, llm: Optional[MockLLM] = None, allow_storage: bool = False, n8n_client: Optional["N8NClient"] = None):
        self.llm = llm or MockLLM()
        self.allow_storage = allow_storage
        self.n8n_client = n8n_client
        self.vars: Dict[str, Any] = {}

    # --------------------------------------------------------------------- #
    # Execution helpers
    # --------------------------------------------------------------------- #
    def _eval_expr(self, expr: str) -> Any:
        """Evaluate expressions in a constrained environment (prototype only)."""
        try:
            return eval(expr, {"__builtins__": {}}, dict(self.vars))
        except Exception as exc:  # pragma: no cover - provide better error later
            raise RuntimeError(f"Expression eval error in '{expr}': {exc}") from exc

    def _eval_kwargs(self, args: str) -> Dict[str, Any]:
        if not args:
            return {}
        try:
            return dict(eval(f"dict({args})", {"__builtins__": {}}, dict(self.vars)))
        except Exception as exc:  # pragma: no cover - de-risked by unit tests later
            raise RuntimeError(f"Failed to parse kwargs for '{args}': {exc}") from exc

    def execute_program(self, program: Program) -> Dict[str, Any]:
        """Execute a program and return the final variable snapshot per task."""
        task_results: Dict[str, Any] = {}
        for task in program.tasks:
            if task.precondition and not self._eval_expr(task.precondition):
                raise RuntimeError(f"Precondition failed for task {task.name}: {task.precondition}")
            for step in task.steps:
                result = self.execute_step(step)
                if step.assignment:
                    self.vars[step.assignment] = result
            if task.postcondition and not self._eval_expr(task.postcondition):
                raise RuntimeError(f"Postcondition failed for task {task.name}: {task.postcondition}")
            task_results[task.name] = dict(self.vars)
        return task_results

    def execute_step(self, step: Step) -> Any:
        """Execute a single step and return its output."""
        action = (step.action or "").lower()

        if action == "fetch":
            arg = step.args or ""
            match = re.search(r'["\'](.*?)["\']', arg)
            url = match.group(1) if match else arg
            return f"fetched({url})"

        if action == "call_llm":
            args = step.args or ""
            match = re.search(r'prompt\s*=\s*"(.*)"', args)
            prompt = match.group(1) if match else args
            prompt = re.sub(r'\{\{([A-Za-z0-9_]+)\}\}', lambda m: str(self.vars.get(m.group(1), "")), prompt)
            return self.llm.call(prompt)

        if action == "store":
            if not self.allow_storage:
                raise RuntimeError("Storage capability not enabled for runtime.")
            return "stored"

        if action == "assert":
            expr = step.args or ""
            if not self._eval_expr(expr):
                raise RuntimeError(f"Assertion failed: {expr}")
            return True

        if action.startswith("n8n."):
            if self.n8n_client is None:
                raise RuntimeError(f"n8n action '{action}' requested but runtime was not initialised with an N8NClient.")
            kwargs = self._eval_kwargs(step.args or "")
            sub_action = action.split(".", 1)[1]
            if sub_action in {"trigger_webhook", "webhook"}:
                path = kwargs.get("path")
                if not path:
                    raise RuntimeError("n8n webhook call requires a 'path' argument.")
                payload = kwargs.get("payload") or kwargs.get("data") or {}
                method = kwargs.get("method", "POST")
                return self.n8n_client.trigger_webhook(path, payload=payload, method=method)
            if sub_action in {"call_workflow", "workflow"}:
                workflow_id = kwargs.get("workflow_id") or kwargs.get("id")
                payload = kwargs.get("payload") or {}
                return self.n8n_client.call_workflow(workflow_id, payload=payload)
            raise RuntimeError(f"Unsupported n8n sub-action '{sub_action}'.")

        if action and "." in action:
            # Treat dotted calls (e.g., news.search) as JSON-friendly log output
            return json.dumps({"tool": action, "args": step.args})

        return step.raw

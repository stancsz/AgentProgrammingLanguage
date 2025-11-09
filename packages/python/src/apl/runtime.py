"""Runtime interpreter for executing APL programs."""

from __future__ import annotations

import json
import os
import re
from typing import Dict, Any, Optional, TYPE_CHECKING

from .ast import Program, Step
from .env import load_env_defaults, resolve_env_value

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
        load_env_defaults()
        self.llm = llm or MockLLM()
        self.allow_storage = allow_storage
        self.n8n_client = n8n_client
        self.vars: Dict[str, Any] = {}

    # --------------------------------------------------------------------- #
    # Execution helpers
    # --------------------------------------------------------------------- #
    def _eval_expr(self, expr: str) -> Any:
        """Evaluate expressions in a constrained environment (prototype only).

        TODO: SECURITY IMPROVEMENT
        - Replace this eval-based implementation with an AST-validated evaluator.
        - Whitelist safe AST node types (e.g. Expression, BoolOp, BinOp, Compare, Name, Load,
          Constant, Subscript, Index) and a small set of safe builtins (len, min, max, sum).
        - Deny attribute access, imports, comprehensions, and arbitrary function calls.
        - Provide clear errors that guide users to safe alternatives.
        This TODO is high-priority for safe production launches.
        """
        try:
            # TODO: temporary prototype behavior — implement AST-safe evaluation here.
            return eval(expr, {"__builtins__": {}}, dict(self.vars))
        except Exception as exc:  # pragma: no cover - provide better error later
            raise RuntimeError(f"Expression eval error in '{expr}': {exc}") from exc

    def _eval_kwargs(self, args: str) -> Dict[str, Any]:
        if not args:
            return {}
        # TODO: SECURITY IMPROVEMENT
        # - Avoid using eval() to parse kwargs. Instead, parse the argument string with a
        #   safe parser (e.g. using ast.parse in 'eval' mode and a constrained AST walker)
        #   or implement a simple key=value parser that handles quoted strings and literals.
        # - Ensure resolve_env_value is only called on validated scalar types.
        try:
            safe_globals = {"__builtins__": {}, "dict": dict}
            # TODO: replace this eval-based parsing with a safe alternative.
            raw = dict(eval(f"dict({args})", safe_globals, dict(self.vars)))
        except Exception as exc:  # pragma: no cover - de-risked by unit tests later
            raise RuntimeError(f"Failed to parse kwargs for '{args}': {exc}") from exc
        return {key: resolve_env_value(value) for key, value in raw.items()}

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
            # TODO: CAPABILITY ENFORCEMENT
            # - Centralize capability checks: verify program-declared capabilities (e.g. storage)
            #   and ToolProxy-provided capability manifests before performing side-effects.
            # - Emit structured audit logs when storage is used (path, requesting task, metadata).
            # - Consider returning a deterministic sentinel or storage metadata instead of
            #   a simple "stored" string in production builds.
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

        if action.startswith("slack."):
            raise RuntimeError(
                "Slack actions are no longer bundled with the APL runtime. "
                "Bind your agent to an MCP Slack server instead (see the MCP registry at https://modelcontextprotocol.io/registry or https://github.com/modelcontextprotocol/registry)."
            )

        if action and "." in action:
            # Treat dotted calls (e.g., news.search) as JSON-friendly log output
            return json.dumps({"tool": action, "args": step.args})

        return step.raw

"""Runtime interpreter for executing APL programs."""

from __future__ import annotations

import json
import os
import re
import ast
from typing import Dict, Any, Optional, TYPE_CHECKING, List
from .integrations.toolproxy import ToolProxy, StorageResult

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

    def __init__(self, llm: Optional[MockLLM] = None, allow_storage: bool = False, n8n_client: Optional["N8NClient"] = None, tool_proxy: Optional["ToolProxy"] = None):
        load_env_defaults()
        self.llm = llm or MockLLM()
        self.allow_storage = allow_storage
        self.n8n_client = n8n_client
        self.tool_proxy = tool_proxy
        self.vars: Dict[str, Any] = {}

    # --------------------------------------------------------------------- #
    # Execution helpers
    # --------------------------------------------------------------------- #
    def _eval_expr(self, expr: str) -> Any:
        """Safely evaluate a restricted expression using ast parsing and validation.

        Allows literals, variable names, boolean/arithmetic ops, comparisons,
        indexing, and calls to a small whitelist of safe functions.
        """
        allowed_funcs = {
            "len": len,
            "min": min,
            "max": max,
            "sum": sum,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
        }

        def _validate_node(node: ast.AST) -> None:
            if isinstance(node, ast.Attribute):
                raise RuntimeError("Attribute access is not allowed in expressions.")
            if isinstance(node, ast.Lambda):
                raise RuntimeError("Lambda expressions are not allowed.")
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
                raise RuntimeError("Import/global/nonlocal statements are not allowed.")
            if isinstance(node, ast.Call):
                if not isinstance(node.func, ast.Name) or node.func.id not in allowed_funcs:
                    raise RuntimeError(f"Function calls are restricted. Allowed: {sorted(allowed_funcs.keys())}")
            if isinstance(node, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                raise RuntimeError("Comprehensions and generator expressions are not allowed.")
            for child in ast.iter_child_nodes(node):
                _validate_node(child)

        try:
            parsed = ast.parse(expr, mode="eval")
            _validate_node(parsed)
            compiled = compile(parsed, "<apl-safe-eval>", "eval")
            safe_globals = {"__builtins__": None}
            safe_globals.update(allowed_funcs)
            return eval(compiled, safe_globals, self.vars)
        except RuntimeError:
            raise
        except Exception as exc:  # pragma: no cover - provide better error later
            raise RuntimeError(f"Expression eval error in '{expr}': {exc}") from exc

    def _eval_kwargs(self, args: str) -> Dict[str, Any]:
        """Parse keyword-style arguments like: key1=val1, key2=val2.

        Values are evaluated using the same AST-safe approach to avoid unsafe eval().
        """
        if not args:
            return {}

        try:
            call_src = f"dict({args})"
            parsed = ast.parse(call_src, mode="eval")
            if not isinstance(parsed, ast.Expression) or not isinstance(parsed.body, ast.Call):
                raise RuntimeError("Malformed kwargs expression.")
            call = parsed.body
            if not isinstance(call.func, ast.Name) or call.func.id != "dict":
                raise RuntimeError("Expected kwargs in key=value form.")

            out: Dict[str, Any] = {}
            for kw in call.keywords:
                if kw.arg is None:
                    raise RuntimeError("Only simple keyword arguments are supported (no **kwargs).")
                expr_node = ast.Expression(body=kw.value)
                ast.fix_missing_locations(expr_node)

                def _validate_node_local(n: ast.AST) -> None:
                    if isinstance(n, ast.Attribute):
                        raise RuntimeError("Attribute access is not allowed in kwargs.")
                    if isinstance(n, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                        raise RuntimeError("Comprehensions are not allowed in kwargs.")
                    if isinstance(n, ast.Call) and not (isinstance(n.func, ast.Name) and n.func.id in {"len", "min", "max", "sum", "int", "float", "str", "bool"}):
                        raise RuntimeError("Function calls in kwargs are restricted.")
                    for c in ast.iter_child_nodes(n):
                        _validate_node_local(c)

                _validate_node_local(expr_node)
                compiled = compile(expr_node, "<apl-safe-kwargs>", "eval")
                safe_globals = {"__builtins__": None, "len": len, "min": min, "max": max, "sum": sum, "int": int, "float": float, "str": str, "bool": bool}
                value = eval(compiled, safe_globals, self.vars)
                out[kw.arg] = resolve_env_value(value)
            return out
        except RuntimeError:
            raise
        except Exception as exc:
            raise RuntimeError(f"Failed to parse kwargs for '{args}': {exc}") from exc

    def execute_program(self, program: Program) -> Dict[str, Any]:
        """Execute a program and return the final variable snapshot per task.

        This method records program context so runtime can enforce declared capabilities
        and provide better runtime diagnostics.
        """
        self._program = program
        # build a quick lookup of declared capabilities per agent
        self._agent_capabilities: Dict[str, List[str]] = {}
        agents_meta = program.meta.get("agents", {})
        for agent_name, info in agents_meta.items():
            self._agent_capabilities[agent_name] = info.get("capabilities", [])

        task_results: Dict[str, Any] = {}
        for task in program.tasks:
            # set current task/agent context for execute_step
            self._current_task = task
            self._current_agent = task.name.split(".", 1)[0] if "." in task.name else None

            if task.precondition and not self._eval_expr(task.precondition):
                raise RuntimeError(f"Precondition failed for task {task.name}: {task.precondition}")
            last_result: Any = None
            for step in task.steps:
                # enforce declared capability requirements for each step
                # NOTE: defer 'storage' checks to execute_step so the runtime can produce
                # consistent, user-facing error messages and allow runtime-level overrides.
                for req in step.requires:
                    if req == "storage":
                        # execute_step will validate storage capability and runtime.allow_storage
                        continue
                    if not self._has_capability(req):
                        raise RuntimeError(f"Missing required capability '{req}' for task '{task.name}' at step: {step.raw}")
                result = self.execute_step(step)
                last_result = result
                if step.assignment:
                    self.vars[step.assignment] = result
            # if the task produced a result but did not assign it to a named variable,
            # expose it under the task's def name (e.g., agent.fn -> 'fn') for convenience
            if last_result is not None:
                def_name = task.name.split(".", 1)[1] if "." in task.name else task.name
                if def_name not in self.vars:
                    self.vars[def_name] = last_result
            if task.postcondition and not self._eval_expr(task.postcondition):
                raise RuntimeError(f"Postcondition failed for task {task.name}: {task.postcondition}")
            task_results[task.name] = dict(self.vars)
        # clear program context
        self._program = None
        self._current_task = None
        self._current_agent = None
        return task_results

    def _has_capability(self, capability: str) -> bool:
        """Return True if the current execution context allows a capability."""
        # runtime-level allow_storage overrides storage capability checks
        if capability == "storage" and getattr(self, "allow_storage", False):
            return True
        agent = getattr(self, "_current_agent", None)
        if agent and hasattr(self, "_agent_capabilities"):
            return capability in self._agent_capabilities.get(agent, [])
        return False

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
            # Centralized storage enforcement using ToolProxy when available.
            kwargs = self._eval_kwargs(step.args or "")
            # Check capability either via runtime override or agent declaration.
            if not (self.allow_storage or self._has_capability("storage")):
                raise RuntimeError("Storage capability not enabled for runtime or declared for the agent.")
            # If a ToolProxy is provided, prefer it for side-effects and auditing.
            if getattr(self, "tool_proxy", None) is not None:
                proxy = self.tool_proxy
                try:
                    provided = proxy.capabilities()
                except Exception:
                    provided = []
                if "storage" not in provided:
                    raise RuntimeError("Bound ToolProxy does not declare 'storage' capability.")
                context = {
                    "task": getattr(getattr(self, "_current_task", None), "name", None),
                    "agent": getattr(self, "_current_agent", None),
                    "program_meta": getattr(getattr(self, "_program", None), "meta", {}),
                }
                result = proxy.perform("store", kwargs, context)
                # Normalize StorageResult or similar structured result
                if isinstance(result, StorageResult):
                    return {"status": result.status, "key": result.key, "meta": result.meta}
                return result
            # Fallback deterministic behaviour for simple runtimes/tests
            if not self.allow_storage:
                raise RuntimeError("Storage capability not enabled for runtime.")
            return {"status": "ok", "key": kwargs.get("key") or kwargs.get("path") or "item", "meta": {"mock": True, "size": len(str(kwargs.get("content") or kwargs.get("value") or ""))}}

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

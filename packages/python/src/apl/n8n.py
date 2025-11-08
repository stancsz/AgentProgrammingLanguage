"""n8n integration helpers for APL."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib import request, error as url_error, parse

from .ast import Program, Task


class N8NError(RuntimeError):
    """Raised when an n8n API call fails."""


class N8NClient:
    """Minimal HTTP client for triggering n8n webhooks and workflows."""

    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _make_url(self, path: str) -> str:
        if not path.startswith("/"):
            path = f"/{path}"
        return parse.urljoin(self.base_url, path)

    def _perform_request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = self._make_url(path)
        data: Optional[bytes] = None
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method=method.upper())
        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except url_error.HTTPError as exc:  # pragma: no cover - network errors require integration tests
            raise N8NError(f"n8n request to {url} failed: {exc.code} {exc.reason}") from exc
        except url_error.URLError as exc:  # pragma: no cover
            raise N8NError(f"n8n request to {url} failed: {exc.reason}") from exc

    def trigger_webhook(self, path: str, payload: Optional[Dict[str, Any]] = None, method: str = "POST") -> Dict[str, Any]:
        if not path:
            raise ValueError("webhook path is required")
        return self._perform_request(method, f"/webhook{path}", payload=payload)

    def call_workflow(self, workflow_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not workflow_id:
            raise ValueError("workflow_id is required")
        # For workflows without explicit webhooks, fall back to default execute endpoint.
        endpoint = f"/workflow/run/{workflow_id}"
        return self._perform_request("POST", endpoint, payload=payload or {})


def _collect_trigger_tasks(program: Program) -> List[Task]:
    tasks: List[Task] = []
    for task in program.tasks:
        meta = task.metadata.get("n8n") if hasattr(task, "metadata") else None
        if not meta:
            continue
        trigger = meta.get("trigger")
        if trigger:
            tasks.append(task)
    return tasks


def to_n8n_workflow(program: Program, runtime_url: str | None = None) -> Dict[str, Any]:
    """
    Transform the subset of tasks annotated with `# n8n: trigger ...` into an n8n
    workflow JSON structure.
    """
    nodes: List[Dict[str, Any]] = []
    connections: Dict[str, Dict[str, List[List[Dict[str, Any]]]]] = {}

    trigger_tasks = _collect_trigger_tasks(program)
    if not trigger_tasks:
        raise ValueError("No tasks annotated with `# n8n: trigger ...` were found.")

    default_runtime_url = runtime_url or "={{ $json.aplRuntimeUrl || $env.APL_RUNTIME_URL }}"

    for index, task in enumerate(trigger_tasks, start=1):
        trigger_meta = task.metadata["n8n"]["trigger"]
        trigger_type = trigger_meta.get("type", "webhook")
        config = trigger_meta.get("config", {})
        node_base_name = task.name.replace(".", "_")
        node_x = 200 * (index - 1)

        if trigger_type != "webhook":
            raise ValueError(f"Unsupported n8n trigger type '{trigger_type}' for task '{task.name}'")

        path = config.get("path") or f"/{node_base_name.lower()}"
        method = config.get("method", "POST").upper()
        webhook_node_name = f"{task.name} Trigger"
        webhook_node = {
            "parameters": {
                "path": path.lstrip("/"),
                "options": {},
                "httpMethod": method,
                "responseMode": config.get("responseMode", "onReceived"),
                "responseDataType": config.get("responseDataType", "json"),
            },
            "id": f"Webhook_{index}",
            "name": webhook_node_name,
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [node_x, 0],
        }
        nodes.append(webhook_node)

        http_node_name = f"{task.name} -> APL Runtime"
        http_node = {
            "parameters": {
                "url": config.get("runtimeUrl", default_runtime_url),
                "options": {},
                "method": "POST",
                "sendBody": True,
                "jsonParameters": True,
                "bodyParametersJson": json.dumps(
                    {
                        "task": task.name,
                        "args": task.args,
                        "steps": [step.raw for step in task.steps],
                    },
                    indent=2,
                ),
            },
            "id": f"HttpRequest_{index}",
            "name": http_node_name,
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 3,
            "position": [node_x, 250],
        }
        nodes.append(http_node)

        connections[webhook_node_name] = {
            "main": [
                [
                    {
                        "node": http_node_name,
                        "type": "main",
                        "index": 0,
                    }
                ]
            ]
        }

    workflow = {
        "name": program.name or "APL Export",
        "nodes": nodes,
        "connections": connections,
        "settings": {
            "executionOrder": "v1",
            "errorWorkflow": program.meta.get("n8n", {}).get("errorWorkflow") if hasattr(program, "meta") else None,
        },
        "meta": {
            "apl": {
                "program": program.name,
                "agents": program.meta.get("agents", {}),
            }
        },
    }
    return workflow

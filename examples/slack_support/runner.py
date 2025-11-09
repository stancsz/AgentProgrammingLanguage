"""FastAPI runner that exposes the slack_support APL agent as an HTTP endpoint.

Quickstart:
1. Copy `examples/slack_support/.env.example` to either `examples/slack_support/.env`
   or the repo root `.env`, then set `SLACK_SUPPORT_API_TOKEN=<random-token>`.
2. `pip install -e .[dev] fastapi uvicorn[standard]`
3. `uvicorn examples.slack_support.runner:app --host 0.0.0.0 --port 8000`
4. Configure the n8n webhook HTTP Request node to call
   `http://localhost:8000/agents/slack-support` with header
   `Authorization: Bearer <same-token>`. Route any Slack delivery through an MCP server
   sourced from the MCP server inventory (https://github.com/modelcontextprotocol/servers).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from apl import Runtime, parse_apl


PROGRAM_PATH = Path(__file__).with_name("slack_support.apl")
PROGRAM = parse_apl(PROGRAM_PATH.read_text(encoding="utf-8"))


def _load_env_files() -> None:
    """Load simple KEY=VALUE pairs from .env files without extra deps."""
    candidates = [
        Path(__file__).with_name(".env"),
        Path(__file__).resolve().parents[1] / ".env",
    ]
    for env_path in candidates:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env_files()
API_TOKEN = os.getenv("SLACK_SUPPORT_API_TOKEN")

try:
    SLACK_SUPPORT_TASK = next(t for t in PROGRAM.tasks if t.name == "slack_support.triage")
except StopIteration as exc:  # pragma: no cover - configuration error
    raise RuntimeError("slack_support.triage task not found in slack_support.apl") from exc


class TicketPayload(BaseModel):
    ticket: str


app = FastAPI(title="APL Slack Support Runner")


def _run_triage(ticket: str) -> Dict[str, Any]:
    runtime = Runtime()
    runtime.vars["ticket"] = ticket
    response_payload: Dict[str, Any] | None = None

    for step in SLACK_SUPPORT_TASK.steps:
        result = runtime.execute_step(step)
        if step.assignment:
            runtime.vars[step.assignment] = result

        raw = step.raw.strip()
        if raw.lower().startswith("return "):
            expr = raw[len("return ") :].strip()
            response_payload = runtime._eval_expr(expr)  # type: ignore[attr-defined]
            break

    if response_payload is None:
        response_payload = dict(runtime.vars)

    return {
        "result": response_payload,
        "variables": dict(runtime.vars),
    }


@app.post("/agents/slack-support")
def triage(payload: TicketPayload, authorization: str | None = Header(default=None)) -> Dict[str, Any]:
    if not payload.ticket:
        raise HTTPException(status_code=400, detail="ticket text is required")
    if API_TOKEN:
        expected = f"Bearer {API_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="invalid or missing token")
    return _run_triage(payload.ticket)

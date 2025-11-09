"""Slack integration helpers."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib import error as url_error, request as url_request

from ..env import load_env_defaults, resolve_env_value


def post_message(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """Send a message via Slack's chat.postMessage API."""
    load_env_defaults()
    resolved = {key: resolve_env_value(value) for key, value in kwargs.items()}

    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN is not set; cannot post to Slack.")

    channel = resolved.get("channel") or os.getenv("SLACK_CHANNEL_ID")
    if isinstance(channel, str) and channel.startswith("#"):
        channel = os.getenv("SLACK_CHANNEL_ID") or channel.lstrip("#")
    if not channel:
        raise RuntimeError("Slack channel not provided; set 'channel' argument or SLACK_CHANNEL_ID.")

    text = resolved.get("text") or resolved.get("message")
    if not text:
        raise RuntimeError("Slack post requires a 'text' (or 'message') argument.")

    payload = json.dumps({"channel": channel, "text": text}).encode("utf-8")
    req = url_request.Request(
        "https://slack.com/api/chat.postMessage",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with url_request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            result = json.loads(body)
    except url_error.HTTPError as exc:
        raise RuntimeError(f"Slack API returned HTTP error {exc.code}: {exc.reason}") from exc
    except url_error.URLError as exc:
        raise RuntimeError(f"Failed to contact Slack API: {exc.reason}") from exc

    if not result.get("ok"):
        raise RuntimeError(f"Slack API error: {result}")
    return result

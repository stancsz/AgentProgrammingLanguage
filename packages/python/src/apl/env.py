"""Environment utilities for the APL runtime/tooling."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

_ENV_LOADED = False


def _iter_candidate_paths() -> Iterable[Path]:
    cwd = Path.cwd()
    repo_root = Path(__file__).resolve().parents[4]
    yield cwd / ".env"
    if repo_root != cwd:
        yield repo_root / ".env"
    yield repo_root / "examples" / "slack_support" / ".env"


def load_env_defaults() -> None:
    """Populate os.environ with KEY=VALUE pairs from common .env locations."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    for env_path in _iter_candidate_paths():
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def resolve_env_value(value: Any) -> Any:
    """Resolve strings of the form 'env:VAR' to environment values."""
    if isinstance(value, str) and value.startswith("env:"):
        return os.getenv(value[4:], "")
    return value

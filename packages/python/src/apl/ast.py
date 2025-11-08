"""Core AST dataclasses for the Agent Programming Language (APL)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class Step:
    """A single executable step within a task."""

    raw: str
    assignment: Optional[str] = None
    action: Optional[str] = None
    args: Optional[str] = None
    requires: List[str] = field(default_factory=list)


@dataclass
class Task:
    """A named task (often an agent function) containing ordered steps."""

    name: str
    args: List[str]
    precondition: Optional[str] = None
    postcondition: Optional[str] = None
    steps: List[Step] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Program:
    """Top-level program containing metadata and tasks."""

    name: str
    meta: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)

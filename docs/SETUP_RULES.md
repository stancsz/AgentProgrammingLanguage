# Setup Rules

## Overview
This document defines the minimum environment and workflow requirements for anyone building or reviewing Agent Programming Language (APL). Follow these rules before writing code or reviewing a pull request.

## Prerequisites
- **Python**: 3.12.x (CPython). Install via pyenv, asdf, or system package manager.
- **Node.js (optional)**: 20.x+ only if working on IDE extensions or web tooling.
- **Git**: Ensure `core.autocrlf=false` to preserve consistent line endings.
- **Make/Invoke**: Not required, but handy for scripting common workflows.

## Environment Setup
1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
   This pulls in the runtime, CLI, tests, `ruff`, `pytest`, `mypy`, and required stubs.
3. Copy environment samples when needed:
   ```bash
   cp examples/slack_support/.env.example examples/slack_support/.env
   ```

## Linting, Typing, and Tests
Run the full loop before any push or PR:
- `ruff check .`
- `mypy packages/python/src`
- `pytest`

Add these commands to your IDE “tasks” or pre-commit workflow. CI will gate on the same trio.

## APL Syntax Highlighting & IDE Support
- **VS Code**: Install (or develop) the `APL Language Support` extension listed in `ROADMAP.md`. Until the extension ships, add to `settings.json`:
  ```json
  {
    "files.associations": {
      "*.apl": "python"
    }
  }
  ```
- **Other IDEs**: Associate `*.apl` with Python highlighting or contribute a Tree-sitter grammar to your editor of choice.
- Enable `ruff` and `mypy` extensions so diagnostics surface inline.

## Command Workflow
1. `python -m apl validate path/to/agent.apl`
2. `python -m apl compile path/to/agent.apl --python-out dist/agent.py --ir-out dist/agent.json`
3. `python -m apl run path/to/agent.apl`
4. Optional packaging targets (wheel/container/serverless) use the same compiled artifacts.

## Repository Rules
- Keep documentation in sync: update `MISSION.md`, `DESIGN_PRINCIPLES.md`, `PRD.md`, `ROADMAP.md`, and `MILESTONE.md` with any user-facing change.
- Do not introduce new external dependencies without updating the PRD and documenting rationale.
- Never add raw credentials; use `.env` indirection plus `env:` references in agent code.
- Preserve deterministic tests. Seed randomness and rely on fixed fixtures for mock LLM outputs.

## Support Channels
- File issues in GitHub with labels `bug`, `dx`, or `design`.
- Use Discussions for proposals that affect language semantics or runtime contracts.
- Document tribal knowledge in the repository instead of private notes.

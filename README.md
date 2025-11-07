# Agent Pseudocode Language (APL) — README

A minimal scaffold and quickstart for the Agent Pseudocode Language (APL) project. This repository contains the language PRD and starter guidance to implement a reference Python runtime, parser, and test harness.

## Goals
- Provide a small, testable pseudocode language for specifying AI task workflows.
- Ship an MVP reference implementation in Python with a mock LLM runtime.
- Provide examples, tests, and CI for deterministic validation.

## Repository layout (recommended)
- apl-spec/             — language spec & grammar (Markdown)
- packages/python/      — Python reference runtime & CLI
  - src/apl/
    - __init__.py
    - parser.py
    - ast.py
    - runtime.py
    - primitives/
    - translator.py
    - cli.py
  - tests/
- examples/             — example .apl programs and golden outputs
- docs/                 — user guides and tutorials
- .github/workflows/    — CI
- README.md
- PRD.md

## Quickstart (Windows, PowerShell / cmd)
```bash
# create and activate venv (cmd.exe)
python -m venv .venv
.venv\Scripts\activate

# install minimal dev deps
pip install lark-parser pytest black ruff
```

## Minimal first files to add
- apl-spec/grammar.md — language grammar + example programs
- packages/python/src/apl/parser.py — tokenizer + minimal parser
- packages/python/src/apl/ast.py — AST node types + IR serializer
- packages/python/src/apl/runtime.py — mock runtime and capability checks
- packages/python/src/apl/cli.py — minimal CLI (validate, run --mock)
- examples/hello.apl — tiny program to parse + run under mock mode

## Development workflow (recommended)
1. Write parsing tests first (pytest) describing expected AST for small APL snippets.
2. Implement parser until tests pass.
3. Implement AST -> IR serializer tests, then runtime mocks.
4. Add CLI and example programs; add golden tests.
5. Configure CI for lint + tests.

## Example: hello.apl (agent-style)

The language uses a Python-like, agent-as-function syntax. Agents can bind MCP/tool servers, define sub-agents, and call other agents. The parser provided in packages/python/src/apl/ supports this style.

```apl
agent hello_world:
  def greet(name):
    msg = call_llm(model="mock", prompt=f"Say hello to {name}")
    assert "hello" in msg.lower()
    return msg

agent data_agent(name) binds mcp.newsapi as news, mcp.storage as s3:
  def run(query):
    articles = news.search(query)                # MCP tool call
    summary = call_llm(model="mock", prompt=f"Summarize: {articles}")
    s3.put(f"bucket/{name}/summary.txt", summary) requires capability.storage
    return summary

agent orchestrator:
  def main():
    scraper = data_agent("scraper")
    result = scraper.run("latest AI news")       # agent-to-agent invocation
    notify = call_llm(model="mock", prompt=f"Notify: {result}")
    return notify
```

Quick CLI (development)
- Validate parsed AST:
  python packages\python\src\apl\__init__.py validate examples\hello.apl
- Translate to LangGraph-like JSON:
  python packages\python\src\apl\__init__.py translate examples\hello.apl
- Run in mock mode:
  python packages\python\src\apl\__init__.py run examples\hello.apl

## Next steps to implement
- Finalize Python-compatible syntax and ensure parser compatibility.
- Implement MCP/tool connectors and a capability manager in runtime.
- Add tests and CI; replace ad-hoc eval with a safe expression evaluator.
- Split scaffold into modules: parser.py, ast.py, runtime.py, cli.py.

## Contact / Contributing
Follow standard PR process. Update PRD.md when changing language semantics.

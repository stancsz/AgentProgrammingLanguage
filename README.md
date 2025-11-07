# Agent Programming Language (APL) - README

A minimal scaffold and quickstart for the Agent Programming Language (APL) project. This repository contains the language PRD and starter guidance to implement a reference Python runtime, parser, and test harness.

## Goals
- Provide a small, testable agent programming language for specifying AI task workflows.
- Ship an MVP reference implementation in Python with a mock LLM runtime.
- Provide examples, tests, and CI for deterministic validation.

## Language foundations
- **Python-aligned surface syntax**: APL adopts Python indentation, expressions, and type annotations so existing Python knowledge transfers. Every agent file is valid UTF-8, uses Python lexical rules, and can embed Python statements in `python:` blocks when needed.
- **First-class agent module system**: Each `agent` declaration is compiled to a Python module object with well-defined imports, exports, and isolated capability scopes. Agents can be packaged, versioned, and distributed through standard Python tooling (wheel, pip).
- **Static capability typing**: All side-effectful primitives carry capability/effect annotations enforced by a static checker before execution. Types are defined with Python-style hints plus agent-specific effects (`Capability[storage]`, `Tool[MCP:newsapi]`).
- **Deterministic compilation pipeline**: Source -> lexer/parser -> typed AST -> capability-annotated IR -> Python `ast` module -> bytecode. Generated Python modules are human-readable and instrumented for replay.
- **Runtime contracts**: Every agent function publishes contracts (input/output types, required capabilities, protocol bindings) that downstream orchestrators can inspect at runtime through reflection APIs.

## Why APL now
- **Protocol-ready agents**: APL lets authors express explicit capabilities, contracts, and message schemas, making it straightforward to target emerging A2A (agent-to-agent), MCP (model context), and AP2 (agent payments) protocols without rewriting business logic. Example:

```apl
agent billing_broker binds a2a.market as registry, mcp.payments as wallet:
  capability ap2.transfer(limit="500.00", currency="USD")

  def hire(invoice_request):
    offer = registry.match(role="accounts_payable", scope=invoice_request.scope)
    quote = offer.negotiate(invoice_request.details)
    wallet.authorise(amount=quote.cost, receipt=invoice_request.id)
    return quote.contract_id
```

- **Programmable multi-agent systems**: Instead of wiring flows in bespoke orchestration code, APL treats agent composition, delegation, and coordination as first-class language constructs, aligning with multi-agent system and AI orchestration patterns. Example:

```apl
agent orchestrator:
  planner = research_planner()
  coder = codegen_agent()
  qa = reviewer_agent()

  def deliver(feature_spec):
    plan = planner.plan(feature_spec)
    implementation = coder.build(plan)
    report = qa.verify(implementation, criteria=plan.tests)
    return { "plan": plan, "implementation": implementation, "qa": report }
```

- **Agentic RAG workflows**: The language captures retrieval strategies, decision checkpoints, and verification steps so that Agentic RAG pipelines become testable programs rather than ad-hoc prompt chains. Example:

```apl
agent research_report:
  def generate(topic):
    search_results = retrieve(query=topic, depth=3)
    filtered = for each doc in search_results where doc.credibility >= 0.8 collect doc
    synthesis = call_llm(model="researcher", prompt=f"Summarise {filtered}")
    assert "sources:" in synthesis.lower()
    return synthesis
```

- **Reasoning frameworks in code**: ReAct, Plan-and-Solve, Reflexion, and related reasoning loops map naturally to APL control flow and metadata, enabling reuse, testing, and deterministic replay of complex reasoning behaviors. Example:

```apl
agent reflexive_solver:
  def solve(task):
    plan = call_llm(model="planner", prompt=f"Plan: {task}")
    result = execute_plan(plan)
    critique = call_llm(model="critic", prompt=f"Review plan {plan} result {result}")
    if "retry" in critique.lower():
      revised = refine_plan(plan, critique)
      return execute_plan(revised)
    return result
```

- **Integration optionality**: APL emits an execution IR that can plug into LangGraph or any other orchestrator - LangGraph is a supported target, not a hard dependency - so teams can adopt existing runtimes while keeping agent intent in portable source code. Example:

```apl
agent export_example:
  metadata backends = ["langgraph", "custom-runtime"]

  def run(inputs):
    step = call_llm(model="orchestrator", prompt=f"Process {inputs}")
    return step
```

## Compilation & runtime overview
- Parse with a deterministic grammar (see `apl-spec/grammar.md`) producing a typed AST.
- Run static analyses: name resolution, capability inference, effect safety, and Python interoperability checks (mypy plugin).
- Emit both a portable IR (JSON) and a Python module (`.py` or bytecode) that shares the same semantics.
- Execute via the reference Python runtime (`apl.runtime`), which enforces capability gates, logs traces, and provides deterministic mock adapters for testing.
- Optional: export IR to LangGraph, CrewAI, or custom orchestrators without losing the source-of-truth agent code.

## Repository layout (recommended)
- apl-spec/             - language spec & grammar (Markdown)
- packages/python/      - Python reference runtime & CLI
  - src/apl/
    - __init__.py
    - parser.py
    - ast.py
    - runtime.py
    - primitives/
    - translator.py
    - cli.py
  - tests/
- examples/             - example .apl programs and golden outputs
- docs/                 - user guides and tutorials
- .github/workflows/    - CI
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
- apl-spec/grammar.md - language grammar + example programs
- packages/python/src/apl/parser.py - tokenizer + minimal parser
- packages/python/src/apl/ast.py - AST node types + IR serializer
- packages/python/src/apl/runtime.py - mock runtime and capability checks
- packages/python/src/apl/cli.py - minimal CLI (validate, run --mock)
- examples/hello.apl - tiny program to parse + run under mock mode

## Development workflow (recommended)
1. Write parsing tests first (pytest) describing expected AST for small APL snippets.
2. Implement parser until tests pass.
3. Implement AST -> IR serializer tests, then runtime mocks.
4. Add CLI and example programs; add golden tests.
5. Run static type/capability checks (mypy plugin + apl check); configure CI for lint + tests.

Quick CLI (development)
- Validate parsed AST:
  python packages\python\src\apl\__init__.py validate examples\hello.apl
- Translate to LangGraph-like JSON (or adapt the IR for other orchestrators):
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

# Agent Programming Language (APL) - README

A statically-typed Domain-Specific Language (DSL) for agent engineering that compiles (or transpiles) to Python.

APL is an open agent-focused programming language that targets the Python ecosystem. The project aims to design, specify, and ship a production-ready language stack—grammar, type system, compiler, runtime, tooling—that lets teams express autonomous agent behavior as audited, testable code and deploy it consistently across laptops, containers, and cloud platforms. This repository is the home for the language specification, reference compiler pipeline, Python runtime, and SDK integrations needed to turn agent research patterns into reliable software artifacts.

## Goals
- Define a Python-aligned agent programming language with formal grammar, static capability typing, and deterministic semantics.
- Deliver a reference compiler pipeline (parser, type checker, Python code generator) and runtime that make APL programs executable, observable, and safe by default.
- Supply tooling—CLI, tests, CI workflows, documentation—that enables teams to author, validate, package, and ship production-grade agent code.
- Make agent deployment straightforward: build once in APL and publish agents to local runtimes, containerized edge workloads, or managed clouds (AWS Lambda/ECS, GCP Cloud Run, Azure Container Apps) without rewriting business logic.

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

- **Integration optionality**: APL emits an execution IR that can plug into LangGraph or any other orchestrator - LangGraph is a supported target, not a hard dependency - so teams can adopt existing runtimes while keeping agent intent in portable source code. Packaging tools turn that source into wheels or containers ready for local hosts or managed clouds. Example:

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
- Package compiled agents into deployable artifacts (wheels, OCI images, serverless bundles) along with capability manifests so they can run locally or on cloud platforms that satisfy the declared runtime contracts.

## Repository layout (recommended)
- apl-spec/             - language spec & grammar (Markdown)
- packages/python/      - Python reference runtime & CLI
  - src/apl/
    - __init__.py
    - __main__.py
    - parser.py
    - ast.py
    - runtime.py
    - ir.py
    - compiler.py
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

# install APL package in editable mode with dev extras
pip install -e .[dev]
```

## Development workflow (recommended)
1. Write parsing tests first (pytest) describing expected AST for small APL snippets.
2. Implement parser and lexer until tests pass.
3. Add type/effect checker coverage, ensuring capability misuse is rejected statically.
4. Generate Python modules and IR artifacts; validate round-trips with golden files.
5. Run static analyses (`apl validate`, mypy plugin) and configure CI gates.
6. Package deployable artifacts (wheels, containers, serverless bundles) and smoke-test them locally.

## Quick CLI (development)
- Validate parsed AST:\
  `python -m apl validate examples\hello.apl`
- Package for deployment (wheel + IR + manifest):\
  `python -m apl compile examples\hello.apl --python-out dist/hello.py --ir-out dist/hello.json`
- Translate to LangGraph-like JSON (or adapt the IR for other orchestrators):\
  `python -m apl translate examples\hello.apl`
- Generate n8n workflow JSON for annotated agents:\
  `python -m apl export-n8n examples\hello.apl --out dist/hello-n8n.json`
- Run in mock mode:\
  `python -m apl run examples\hello.apl`

## Next steps to implement
- Finalize Python-compatible syntax and ensure parser compatibility.
- Implement MCP/tool connectors, capability manager, and hardened sandbox runtime.
- Build packaging/distribution tooling for containers and serverless targets.
- Add type/effect checker, CI automation, and expanded documentation to support production deployment.
- Publish SDK examples demonstrating deployment to local, container, and serverless environments.

## Examples
- `examples/hello.apl` — Introductory language tour (parsing, MCP calls, sub-agents).
- `examples/n8n_webhook.apl` — Minimal n8n-triggered notifier agent.
- `examples/slack_support/slack_support.apl` — Slack ticket triage with knowledge-base updates.
- `examples/customer_support.apl` — Email/CRM escalation workflow.
- `examples/coding_expert.apl` — Code-review assistant for GitHub PRs.
- `examples/github_agent.apl` — Issue grooming and label suggestions.
- `examples/incident_responder.apl` — PagerDuty + Slack incident handler.
- `examples/release_brief.apl` — Automated release note publisher.
- `examples/data_pipeline_monitor.apl` — Pipeline health summariser.
- `examples/meeting_scheduler.apl` — Calendar coordination and email drafting.
- `examples/lead_qualification.apl` — Lead scoring and sales notification.
- `examples/knowledge_curator.apl` — Search synthesis to feed internal KBs.
- `examples/slack_support/runner.py` — FastAPI runner that exposes the Slack support agent.

## n8n integration (experimental)
- Annotate agent entrypoints with inline comments to describe how they should surface inside n8n:

  ```apl
  agent notifier:
    # n8n: trigger webhook path="/apl/notifier" method="POST"
    def run(payload):
      response = n8n.workflow(workflow_id="slack-notify", payload=payload)
      return response
  ```

- Run `python -m apl export-n8n your_agent.apl --out dist/workflow.json` to emit an n8n workflow definition pairing each trigger with an HTTP Request node that calls back into the APL runtime (override the target with `--runtime-url`).
- Initialise `apl.runtime.Runtime` with an `N8NClient` to reuse authenticated connectors:

  ```python
  from apl.n8n import N8NClient
  from apl.runtime import Runtime

  client = N8NClient(base_url="https://n8n.example.com", api_key="<api-key>")
  runtime = Runtime(n8n_client=client)
  ```

- Within agent code, call `n8n.webhook(...)` or `n8n.workflow(...)` steps to delegate triggers/actions to n8n while keeping APL agents lightweight.
- To drive agents behind HTTP endpoints:\
  1. Copy `examples/slack_support/.env.example` to either `examples/slack_support/.env` or the repo root `.env`, then set `SLACK_SUPPORT_API_TOKEN=<random-token>` and fill Slack credentials.\
  2. Install extras: `pip install -e .[dev] fastapi uvicorn[standard]`.\
  3. Run `uvicorn examples.slack_support.runner:app --host 0.0.0.0 --port 8000`.\
  4. Configure the n8n HTTP Request node to call `http://localhost:8000/agents/slack-support` with header `Authorization: Bearer <same-token>` while its Slack node posts the formatted reply.

## Contact / Contributing
Follow standard PR process. Update PRD.md when changing language semantics.

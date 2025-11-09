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
- Why a language (not only a package): libraries and frameworks can glue tools together, but they do not provide a single, auditable source-of-truth for agent intent, effects, and capabilities. A language lets you express contracts, capability requirements, and inter-agent protocols as first-class, statically-checkable constructs. That makes agents portable, reviewable, and safe by default — properties that ad-hoc packages and recipes struggle to guarantee.

- Stability across surface churn: tool APIs, SDKs, and runtime services evolve rapidly. APL decouples intent (what the agent should do and what capabilities it needs) from any single runtime or SDK implementation. The compiler and runtime become a stable translation layer that adapts to changing integrations without rewriting business logic.

- Static safety and observability: encoding side-effects and permissions in the language enables static checks (rejecting unauthorized storage or external calls), capability manifests, and richer runtime contracts. These guarantees are hard to achieve reliably with a loose collection of packages.

- Composition and low-code agent development: APL treats agent composition, delegation, and capability bindings as language primitives. That lowers the barrier to creating and reusing agents (low-code), and it makes generated or human-written agents easier for LLMs and operator tools to understand, validate, and deploy quickly.

- Faster iteration for AI-driven development: when agents are expressed as concise, typed source, AI tooling can inspect, refactor, and synthesize agents more reliably. This improves automation in testing, code generation, and deployment pipelines so new agents can be produced and verified faster than when using unstructured code + config.

- Portability & integration-first design: APL compiles to a portable IR and Python artifacts that can target local runtimes, containers, or managed services. That portability, paired with formal capability manifests, makes it straightforward to adopt new runtimes or registry-based integrations (MCP/A2A) without changing agent source.

Short example (intent vs implementation):

```apl
agent billing_broker binds mcp.payments as wallet:
  capability payments.charge

  def hire(invoice):
    # intent: charge the invoice source; runtime enforces capability and binding
    charge_result = wallet.charge(amount=invoice.total, id=invoice.id)
    return charge_result.receipt
```

This separation (intent + capability + binding) is what a package alone cannot guarantee at compile time or in CI; a language gives you that guarantee, enabling safer, faster, and more reproducible agent development.

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
- `examples/slack_support/test_post_message.apl` — Minimal program that posts a Slack message via `apl run`.

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
  1. Copy `examples/slack_support/.env.example` to either `examples/slack_support/.env` or the repo root `.env`, then set `SLACK_SUPPORT_API_TOKEN=<random-token>`.\
  2. Install extras: `pip install -e .[dev] fastapi uvicorn[standard]`.\
  3. Run `uvicorn examples.slack_support.runner:app --host 0.0.0.0 --port 8000`.\
  4. Configure the n8n HTTP Request node to call `http://localhost:8000/agents/slack-support` with header `Authorization: Bearer <same-token>` and route downstream delivery through an MCP Slack server (consult the MCP registry: https://modelcontextprotocol.io/registry or https://github.com/modelcontextprotocol/registry).
- Provision Slack access by deploying or registering an MCP Slack server from the registry and binding it in APL (`binds mcp.slack as slack`). The runtime no longer bundles Slack credentials; authentication and delivery live with the MCP integration.

## Contact / Contributing
Follow standard PR process. Update PRD.md when changing language semantics.

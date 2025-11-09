# Agent Programming Language (APL) - Product Requirements Document

## 1. Summary
Agent Programming Language (APL) exists so that a team can define, run, and ship a production agent with fewer than 40 lines of source and a single deployment command. The language stays Python-aligned on purpose: every construct can be linted with standard Python tooling, formatted with opinionated formatters, and statically analysed alongside host Python code. The runtime honours capability gating, deterministic testing (mock LLMs), and packaging targets ranging from laptops to containers and serverless environments, keeping the authoring surface declarative while enforcing safety by default.

APL’s current iteration focuses on closing the tooling gap discovered in Issue #16 (Design audit: improve MCP discovery, tool adapters, and runtime capability model). The reference implementation must own structured tool resolution, safe evaluation without `eval`, explicit capability enforcement, and IDE ergonomics (syntax highlighting, linting) so that shipping an agent feels the same as shipping a high-quality Python microservice.

## 1.1 Language Definition Goals
- **Python surface compatibility**: Every valid APL program conforms to Python lexical rules and can be linted/pretty-printed with Python tooling; invalid constructs should produce Python-esque diagnostics.
- **Static capability/effect typing**: Side-effectful primitives require declared capabilities; the type checker enforces capability flow, effect subtyping, and input/output contracts.
- **Module and package system**: Agents compile to Python packages with import/export directives, version metadata, and dependency manifests (`apl.toml`) to enable pip-style distribution.
- **Deterministic semantics**: Evaluation order, scoping, and runtime behavior must be defined formally (operational semantics document + executable reference tests).
- **Bidirectional interop**: APL code can call Python libraries through safe adapters; Python hosts can embed and invoke APL agents through the generated module artifacts.

## 1.2 Modern Agent Ecosystem Drivers
- **Protocol alignment (A2A, MCP, AP2)**: APL provides explicit constructs for declaring agent capabilities, contracts, and payment flows so the same source program can target agent-to-agent protocols, tool-facing model context protocols, and emerging payments rails without embedding protocol specifics in business logic.
- **Multi-agent systems & orchestration**: Task decomposition, sub-agent composition, and coordination semantics are expressed as code, giving AI orchestration layers a deterministic contract for delegation, retries, and audit while keeping the orchestration engine (LangGraph or alternatives) pluggable.
- **Agentic RAG**: Retrieval intents, query refinement loops, and verification gates are encapsulated as reusable language patterns, enabling deterministic testing and golden traces for research-style agentic RAG workflows.
- **Reasoning frameworks (ReAct, Plan-and-Solve, Reflexion)**: Control-flow primitives and metadata allow these reasoning loops to be encoded, versioned, and validated within APL, instead of being hidden in prompts or bespoke Python glue.
- **Extensibility for future standards**: By separating declarative agent intent from execution backends, APL keeps room for new interoperability layers, marketplaces, or simulation environments while preserving a single source of truth for agent behavior.
- **Deployment agility**: Portable code generation and packaging make it straightforward to ship the same agent to laptops, Kubernetes clusters, or serverless runtimes while honoring declared capabilities and policies.

## 1.3 Current Focus (Issue #16: Tooling & Safety Audit)
- Introduce a first-class `ToolRegistry` and `ToolProxy` abstraction that owns registration, discovery, invocation, and telemetry for all bound tools.
- Implement an MCP resolver that maps `binds mcp.*` statements to registry metadata, creates `MCPToolProxy` instances, and caches credentials/configuration overrides.
- Replace the dotted-call heuristic in `Runtime.execute_step` with structured dispatch that surfaces deterministic errors, contracts, and capability checks.
- Add a `CapabilityManager` that enforces declarative capability manifests at runtime and powers future static analysis.
- Replace `eval`-based expression parsing with a safe literal/AST evaluator and ensure kwargs resolution is sandboxed.
- Ship regression tests for bind resolution, tool dispatch, and unsafe-eval prevention.
- Deliver editor ergonomics: Python linting via `ruff`, syntax highlighting (Tree-sitter grammar + VS Code extension), and language server roadmap entries.

## Expert Design Review (Programming Language Perspective)
- **Purpose alignment**: The repository communicates APL as a full Agent Programming Language. Maintain strict naming consistency across documentation and tooling to avoid scope drift and to reinforce that the goal is a programmable, testable agent language rather than an informal notation.
- **Semantics contract (Sections 2, 7)**: The language overview would benefit from an explicit definition of the core semantic model: evaluation order, scoping rules for agent/task definitions, and the lifecycle of variables across nested agents. Without this contract the translator and runtime risk diverging. Recommend adding a normative semantics appendix that describes the execution model in prose plus illustrative state diagrams.
- **Type and capability systems (Sections 6, 7, 10)**: The current requirements mention "simple typed values" but do not articulate a type discipline. Even a lightweight structural typing scheme or effect annotations for steps would tighten the safety story. Consider introducing capability-annotated type signatures (e.g., `call_llm :: Prompt -> Capability[llm] -> Response`) to give both the interpreter and static tooling a consistent surface.
- **Deterministic testing and mocks (Sections 4, 8, 13)**: Determinism hinges on reproducible inputs, seeded randomness, and trace capture. Document how mocked LLM responses are versioned and selected, how prompt deltas are diffed, and how to surface divergence between mock and live runs. A recommendation is to mandate golden snapshots for IR plus execution traces in the MVP.
- **Composable tooling (Sections 5, 9)**: MCP binding is central but under-specified. Outline the contract between APL and MCP servers (authentication, schema discovery, error propagation). Suggest introducing a capability declaration syntax that maps cleanly to MCP metadata to enable static validation before runtime.
- **Control flow and concurrency (Section 7)**: While minimal control flow is listed, there is no guidance on asynchronous steps, parallel compositions, or cancellation semantics. Consider a follow-on task to define `parallel` and `race` constructs or, at minimum, document how the runtime serializes steps and whether steps may interleave IO.
- **Versioning and backward compatibility (Sections 11, 12)**: Add a clear versioning policy for both the language and reference runtime (semantic versioning or similar) plus migration guidelines. Early adopters will need to reason about compatibility when upgrading from MVP to v1.
- **Tooling roadmap (Sections 11, 12, 16)**: The roadmap should call out a reference formatter, linter, and language server plans earlier. These developer ergonomics strongly influence adoption and surface many semantic inconsistencies during authoring.
- **Safety posture (Sections 6, 14)**: Expand on how sandboxing is enforced (process isolation vs policy checks) and how capability misuse is reported. Recommend adding threat modeling milestones and automated policy tests to the MVP backlog.

## 2. Objectives
- Provide a concise language for specifying tasks, pre/post conditions, and sub-tasks.
- Enable deterministic translation into prompts or a constrained runtime for LLM execution.
- Ship an MVP that includes language spec, parser, runtime translator, test harness, and examples.

## 3. Stakeholders
- Product owner / researcher
- Engineers (language, infra)
- QA / evaluators
- Early integrators (apps that want controlled LLM agents)

## 4. Success Metrics
- Author-to-deploy path: showcase agent runs that go from `.apl` source to a deployed runtime in ≤40 lines of code and ≤5 terminal commands (validate → lint → compile → package → run).
- Tool resolution: 100% of declared `binds` resolve through `ToolRegistry` or fail-fast with actionable diagnostics; unit tests cover ≥90% of registry and proxy code branches.
- Safety: zero dynamic `eval` usage in runtime paths; capability gating verified by automated tests and documented threat models.
- Tooling ergonomics: repository passes `ruff check`, `mypy`, and formatting hooks in CI; `.apl` files render with syntax highlighting and linting inside VS Code and other major IDEs.
- Determinism: reference agents run identically across local, container, and serverless targets with captured execution traces for replay.

## 5. Use Cases
- Compose multi-step data processing tasks (fetch, transform, summarise).
- Define conditional task flows and retries for LLM actions.
- Provide assertions and test cases for expected outputs.
- Provide audit logs and deterministic replay.

## 6. Requirements

Functional:
- Human-readable syntax for tasks, steps, variables, control flow, assertions.
- Parser that emits an AST and JSON/YAML IR.
- Translator that maps AST to LLM prompts or to an interpreter runtime, with pluggable backends for LangGraph and other orchestration targets.
- Test harness that runs examples deterministically (with mock LLM).
- CLI to validate, lint, run, and test APL scripts.
- Structured tool management: `ToolRegistry` + `ToolProxy` abstractions for registering, resolving, and invoking bound tools with tracing hooks.
- MCP resolver that hydrates proxies from registry metadata, supports offline caches, and exposes typed capability manifests.
- Runtime `CapabilityManager` that enforces declared capabilities and surfaces violations before execution.
- Safe expression and kwargs evaluation that relies on literal/AST parsing instead of Python `eval`.
- Static type checker (Python-aligned syntax + capability/effect system) and code generator that emits human-readable Python modules (`.py`) as well as portable IR artifacts.
- Packaging toolchain to produce deployable artifacts (wheels, OCI images, serverless bundles) with embedded capability manifests and environment requirements.

Non-functional:
- Secure defaults (no external side-effects by default).
- Extensible: allow custom actions/primitive operations.
- Portable: implement reference runtime in Python (primary) and Node.js (optional).
- Simple: keep syntax minimal to reduce parsing complexity.
- Deployable: generated artifacts must run consistently across local machines, container platforms, and major clouds (AWS, GCP, Azure) with configuration-driven capability provisioning.
- Low-friction authoring: maintain ≤40-LOC baseline examples and keep CLI workflows opinionated and scriptable.
- IDE support: provide syntax highlighting (Tree-sitter grammar + VS Code extension), file associations, and linting hooks that reuse Python tooling.

Safety & Governance:
- Explicit capability model: any action that does IO or network must be allowed in runtime flags.
- Assertions and capability checks included in language runtime.
- Audit logs with source mapping to original APL lines.

## 7. Language Design (high-level)

Core concepts:
- program: named collection of tasks
- task: sequence of steps with inputs/outputs
- step: primitive action (e.g., call_llm, fetch, compute, assert)
- variables: simple typed values (string, number, list, map)
- control flow: if, for, while (minimal)
- error handling: retry N times, on_error blocks
- metadata: preconditions, postconditions, capabilities

Example APL (illustrative):

```apl
# Python-like, agent-as-function (Python-compatible style)
agent summarize_and_store(version="0.1"):

  def fetch_transform_store(url):
    precondition: url != ""
    raw = fetch(url)
    summary = call_llm(model="gpt-4", prompt=f"Summarize: {raw}")
    assert len(summary) > 0
    store("s3://bucket/key", summary) requires capability.storage

# Bind MCP/tool servers and use them like attributes on objects
agent data_agent(name) binds mcp.newsapi as news, mcp.storage as s3:

  def run(query):
    articles = news.search(query)            # MCP tool call
    summary = call_llm(model="gpt-4", prompt=f"Summarize: {articles}")
    s3.put("bucket/key", summary) requires capability.storage

# Sub-agent composition and agent-to-agent calls
agent orchestrator:

  sub = data_agent("scraper")                # compose a sub-agent
  result = sub.run("latest ai news")        # agent-to-agent invocation
  notify = call_llm(model="gpt-4", prompt=f"Notify: {result}")

# Lightweight fallback: single-line steps are treated as call_llm prompts
agent loose_example:
  "Search latest research and summarise for me"   # becomes call_llm fallback
```

## 8. Execution Model
- Parse APL -> AST -> IR (JSON)
- Perform static analysis: name resolution, type inference, capability/effect validation
- Emit Python AST/module and portable IR artifacts
- Runtime validates capabilities & preconditions
- Two execution modes:
  - Simulated (mocked LLMs) for testing and CI
  - Live (LLM-backed) with capability gating and resource controls
- Translator approach:
  - Direct interpreter (execute built-in primitives)
  - Prompt-emitting translator (convert tasks to a single structured prompt for LLM orchestration)
  - Optional adapters that emit LangGraph, CrewAI, or other orchestrator-friendly graphs (LangGraph is treated as a first-class integration target, not the sole runtime)
  - Deployment artifact generation (wheel bundles, OCI images, serverless descriptors) with capability manifests for target environments

## 9. Architecture & Components
- Language spec (YAML/Markdown)
- Lexer & Parser -> AST
  - Use small handwritten parser (Python + lark or tree-sitter grammar) for MVP
- Type checker & capability analyzer (mypy plugin or custom)
- IR serializer (JSON)
- Python code generator (APL AST -> Python `ast` -> `.py` module)
- Runtime / Executor
  - Primitive implementations (call_llm, fetch, store, compute, assert)
  - Capability manager & sandbox
- Packaging & Deployment
  - Wheel/SDist builder embedding capability manifests
  - Container/serverless templates for AWS/GCP/Azure and on-prem schedulers
- CLI (validate, check, package, run, test)
- Test harness (unit + integration with mocked LLM)
- Docs & examples

## 10. Tech Stack Recommendations
- Reference implementation: Python 3.10+
  - Parser libs: lark, or use ANTLR with Python target
  - Type checking: mypy plugin / pyright extension for APL, leveraging Python typing rules
  - Code generation: Python `ast` / `black` for emitting canonical module code
  - Packaging: hatch/poetry for wheels, docker buildx for container images, serverless templates (AWS SAM, GCP Cloud Run, Azure Container Apps) for managed deployment
  - Virtual environment: poetry or pip + venv
- Optional: TypeScript implementation for browser/Node integration
- CI: GitHub Actions (lint, unit tests, integration with fake LLM)
- Testing: pytest, snapshots for example outputs, mypy/pyright checks
- Linting: black, ruff (Python)

## 11. Repo Layout (recommended)
- /apl-spec/          # language spec (markdown + grammar)
- /packages/python/   # reference runtime & CLI
  - src/apl/
    - parser.py
    - ast.py
    - runtime.py
    - primitives/
    - translator.py
  - tests/
- /examples/          # example APL programs and golden outputs
- /docs/              # usage, spec, tutorials
- .github/workflows/
- README.md
- PRD.md

## 12. Implementation Roadmap (Phases)
MVP (weeks 0–6)
- Language spec draft
- Reference parser + AST
- IR JSON serializer
- Minimal runtime: call_llm (mock), assert, variables, simple store primitive (local)
- CLI: validate & run (mock mode)
- 5 example programs + tests

v1 (weeks 6–14)
- Real LLM integration with prompt templates
- Capability manager & sandbox
- Retry & error handling primitives
- CI with mocked LLM and coverage

v2+
- TypeScript runtime
- Web playground + VSCode extension (language server)
- Formal verification tooling & deterministic replay

## 13. Testing & Evaluation
- Unit tests for parser, AST, runtime primitives
- Integration tests with mocked LLM responses
- Golden tests for example programs
- Metrics: parse success rate, test pass rate, execution reproducibility

## 14. Risks & Mitigations
- Ambiguous language semantics — mitigate with formal spec and examples.
- LLM non-determinism — mitigate via structured prompts, constraints, retries, and verification steps.
- Security risk from primitives — default deny capabilities; require explicit enable for IO.

## 15. First Development Tasks (short-term)
1. Draft spec: syntax + grammar (apl-spec/grammar.md)
2. Create repo and Python package scaffold
3. Implement tokenizer + minimal parser (parse variables, steps, tasks)
4. Implement type checker skeleton (name resolution, capability declarations, Python interop stubs)
5. Emit AST -> IR JSON + Python module
6. Build packaging pipeline (wheel/SDist builder, OCI/Docker template, serverless manifest generator)
7. Implement mock runtime with call_llm (deterministic stub) and assert
8. Add CLI: apl validate <file>, apl check <file>, apl package <file>, apl run --mock <file>
9. Add 5 example programs + tests
10. Add CI pipeline for lint + tests + static checking
11. Write README + contribution guide
12. Publish MVP branch + release notes

## 17. Integration Inventory (external building blocks)
APL aims to interoperate with leading open-source agent tooling. Repositories cloned under `_external/` provide reference integrations and adapters across the agent stack:
- Core frameworks & orchestration: `langchain-ai/langchain`, `openinterpreter/open-interpreter`, `microsoft/autogen`, `run-llama/llama_index`, `crewAIInc/crewAI`, `langchain-ai/langgraph`.
- LLM abstraction & serving: `ollama/ollama`, `vllm-project/vllm`, `BerriAI/litellm`.
- Memory & knowledge stores: `milvus-io/milvus`, `qdrant/qdrant`, `chroma-core/chroma`, `weaviate/weaviate`.
- Tooling & action providers: `microsoft/playwright`, `modelcontextprotocol/python-sdk`.
- Structured data & validation: `pydantic/pydantic`, `567-labs/instructor`.
- Evaluation, tracing, observability: `confident-ai/deepeval`, `explodinggradients/ragas`, `arize-ai/phoenix`, `langchain-ai/langsmith-sdk`.

SDKs and adapters should be developed so that APL capability manifests can bind to these libraries with minimal glue code, preserving the declarative nature of agent definitions.

## 17. Developer Guidance & Directions

Refer to `SETUP_RULES.md` for the full environment contract. Quick start:
1. Use Python 3.12 and create/activate a virtual environment (`python -m venv .venv`, then `.venv\Scripts\activate` on Windows or `source .venv/bin/activate` on Unix).
2. Install dependencies with `pip install -e .[dev]` to pull in runtime code, `ruff`, `pytest`, `mypy`, and development stubs.
3. Run the fast feedback loop before pushing:
   - `ruff check .`
   - `mypy packages/python/src`
   - `pytest`
4. Compile and execute agents end-to-end:
   - `python -m apl validate path/to/agent.apl`
   - `python -m apl compile path/to/agent.apl --python-out dist/agent.py --ir-out dist/agent.json`
   - `python -m apl run path/to/agent.apl`
5. Configure editor support:
   - Install the forthcoming "APL Language Support" VS Code extension (see `ROADMAP.md`), or temporarily map `*.apl` to Python in `settings.json`.
   - Enable `ruff` and `mypy` VS Code integrations so `.apl`-generated Python emits diagnostics inline.
6. Keep docs in sync: update `MISSION.md`, `DESIGN_PRINCIPLES.md`, `ROADMAP.md`, `MILESTONE.md`, and relevant examples whenever behavior or workflows change.

Suggested implementation order for major features:
1. Language spec & conformance tests.
2. Tooling primitives (ToolRegistry, MCP resolver, CapabilityManager, safe evaluators).
3. Runtime orchestration and adapter plugins.
4. Packaging, deployment surfaces, and CLI ergonomics.
5. Sample agents + scenario tests that demonstrate the <40 LOC deployment path.

## 18. Example contributor checklist (for PRs)
- [ ] Link an issue or milestone and update `ROADMAP.md` if scope changes.
- [ ] Add/update spec entry if syntax or semantics change.
- [ ] Add parser/type/runtime tests covering new behavior (ToolRegistry and capability flows when relevant).
- [ ] Run `ruff`, `mypy`, and `pytest`; capture outputs in the PR description.
- [ ] Update docs (`MISSION.md`, `DESIGN_PRINCIPLES.md`, `PRD.md`, examples) and refresh sample agents if behavior changes.

## 19. Next immediate deliverables
- Issue #16 alignment: land `ToolRegistry` plumbing with runtime dispatch replacement and regression tests.
- Safety milestone: replace `eval`-based evaluation with literal/AST parsing safeguarded by the CapabilityManager.
- MCP integration: implement registry client + proxy stack with fixture-based tests and documented override strategy.
- Editor ergonomics: publish interim VS Code configuration snippet, outline Tree-sitter grammar milestones, and ensure `.apl` files highlight correctly.
- Deployment path demo: maintain a reference agent (<40 LOC) that validates → lints → compiles → packages → runs inside a containerised mock runtime.

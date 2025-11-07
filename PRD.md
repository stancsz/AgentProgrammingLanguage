# Agent Programming Language (APL) - Product Requirements Document

## 1. Summary
Create a small, safe, and testable agent programming language for specifying, composing, deploying, and managing agents (Agent Programming Language - APL). APL is designed to be the "glue" for building agent systems: a Python-like, intentionally lightweight syntax (Python-compatible where practical) that lets authors define agents as first-class "agent" functions, compose sub-agents, bind MCP servers and external tools, and express agent-to-agent interactions. APL translates deterministically to execution representations (including a LangGraph-compatible IR), supports MCP/tool invocation, capability gating, sandboxing, deterministic testing (mock LLMs), and fast deployment and orchestration of agents.

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
- MVP: parse >90% of authoring samples without errors.
- Execution: end-to-end task runs reproduce expected outputs in >=70% of test cases.
- Safety: sandboxing prevents network or filesystem access unless explicitly allowed.
- Usability: clear docs and 5 example end-to-end workflows.

## 5. Use Cases
- Compose multi-step data processing tasks (fetch, transform, summarise).
- Define conditional task flows and retries for LLM actions.
- Provide assertions and test cases for expected outputs.
- Provide audit logs and deterministic replay.

## 6. Requirements

Functional:
- Human-readable syntax for tasks, steps, variables, control flow, assertions.
- Parser that emits an AST and JSON/YAML IR.
- Translator that maps AST to LLM prompts or to an interpreter runtime.
- Test harness that runs examples deterministically (with mock LLM).
- CLI to validate, lint, run, and test APL scripts.

Non-functional:
- Secure defaults (no external side-effects by default).
- Extensible: allow custom actions/primitive operations.
- Portable: implement reference runtime in Python (primary) and Node.js (optional).
- Simple: keep syntax minimal to reduce parsing complexity.

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
- Runtime validates capabilities & preconditions
- Two execution modes:
  - Simulated (mocked LLMs) for testing and CI
  - Live (LLM-backed) with capability gating and resource controls
- Translator approach:
  - Direct interpreter (execute built-in primitives)
  - Prompt-emitting translator (convert tasks to a single structured prompt for LLM orchestration)

## 9. Architecture & Components
- Language spec (YAML/Markdown)
- Lexer & Parser -> AST
  - Use small handwritten parser (Python + lark or tree-sitter grammar) for MVP
- IR serializer (JSON)
- Runtime / Executor
  - Primitive implementations (call_llm, fetch, store, compute, assert)
  - Capability manager & sandbox
- CLI (validate, run, test)
- Test harness (unit + integration with mocked LLM)
- Docs & examples

## 10. Tech Stack Recommendations
- Reference implementation: Python 3.10+
  - Parser libs: lark, or use ANTLR with Python target
  - Virtual environment: poetry or pip + venv
- Optional: TypeScript implementation for browser/Node integration
- CI: GitHub Actions (lint, unit tests, integration with fake LLM)
- Testing: pytest, snapshots for example outputs
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

## 15. First 10 Development Tasks (short-term)
1. Draft spec: syntax + grammar (apl-spec/grammar.md)
2. Create repo and Python package scaffold
3. Implement tokenizer + minimal parser (parse variables, steps, tasks)
4. Emit AST -> IR JSON
5. Implement mock runtime with call_llm (deterministic stub) and assert
6. Add CLI: apl validate <file>, apl run --mock <file>
7. Add 5 example programs + tests
8. Add CI pipeline for lint + tests
9. Write README + contribution guide
10. Publish MVP branch + release notes

## 16. Developer Guidance & Directions (how to start)

Minimal immediate steps (commands are suggestions — pick venv manager of choice):
- Create repo and a Python package:
  - python -m venv .venv
  - .venv\Scripts\activate
  - pip install lark-parser pytest black ruff
- Create files:
  - apl-spec/grammar.md
  - packages/python/src/apl/parser.py
  - packages/python/src/apl/ast.py
  - packages/python/src/apl/runtime.py
  - examples/hello.apl
  - README.md
- Implement a tiny parser that can parse:
  - program/task/step/variable/assignment/assert lines
- Implement runtime with a mocked call_llm that returns deterministic output from fixtures.
- Wire CLI using argparse or click to expose validate/run/test.

Suggested development order:
1. Spec -> tests that describe parsing expectations (TDD).
2. Parser -> pass parsing tests.
3. AST -> IR serializer tests.
4. Runtime with mock LLM -> integration tests for example scripts.
5. CI and docs.

## 17. Example contributor checklist (for PRs)
- [ ] Add/update spec entry if syntax changes
- [ ] Add parser tests for new syntax
- [ ] Update runtime tests if behavior changes
- [ ] Documentation updated
- [ ] Add example program demonstrating feature

## 18. Next immediate deliverable
- Create repository skeleton, grammar.md, and a "hello world" APL example that parses and runs in mock mode.

# Design Principles

## Python-First Ergonomics
APL mirrors Python’s indentation, expressions, and type hints so existing linting (`ruff`, `mypy`), formatting, and IDE behavior apply automatically. Any APL syntax addition must pass the “Python linter friendly” check.

## Deterministic by Default
Compilation, runtime evaluation, and tool dispatch must produce reproducible results. Every command captures sufficient trace data to replay an agent run and to diff changes across versions.

## Safety Over Magic
Capability declarations, sandbox flags, and safe evaluators guard against unintended IO, network, or credential exposure. Disallow `eval`/`exec`, require explicit capability approval, and fail fast with diagnostics that explain how to remediate.

## Composable Tooling
All integrations (MCP, HTTP clients, SaaS APIs) flow through a `ToolRegistry`/`ToolProxy` contract with typed capability manifests. Adapters are pluggable modules, not hard-coded branches of the runtime.

## Opinionated Yet Extensible
Provide a strong default CLI, packaging pipeline, and deployment templates, while letting teams opt into custom adapters, runners, or orchestration targets through documented extension points.

## Observable Execution
Each agent run should emit structured logs, capability usage, and tool call telemetry. Observability hooks are designed into the runtime and compiler so production operators can audit behavior without instrumenting downstream systems.

## Documentation as a Feature
Every new language feature or runtime capability ships with updated `PRD.md`, examples, and developer guides. Docs must explain *why* a change exists, not just *how* to call it.

---

# Launch & Scale Strategy (added)

This section captures practical principles and a prioritized strategy for launching APL as a production-ready DSL that can be adopted and scaled across teams.

## Strategic Principles
- Security-first: no artifact shipped or executed without passing a safety gate. Side-effects must be explicit and gated by declared capabilities.
- Minimal stable surface: keep core language small and stable; place experimental features behind flags and opt-in grammar extensions.
- Adapter-driven ecosystem: provide a small, well-documented adapter SDK so third parties can integrate without modifying core runtime.
- Strong ergonomics: fast onboarding (examples + templates), deterministic compile/run experience, and good editor feedback (diagnostics/LSP).
- Observable, auditable execution: IR provenance, execution traces, and capability usage logs are first-class outputs.

## Roadmap — High level
- Phase 0 (critical): safety and CI baseline
  - Replace unsafe evaluators with AST-safe evaluation.
  - Add IR schema validation and include ir_version / ir_hash in artifacts.
  - Add CI: lint, typecheck, tests, IR validation.
- Phase 1 (core): deterministic parser & runtime contracts
  - Move parser to a grammar (Lark), produce AST with source positions.
  - Implement ToolProxy, capability manifests, and enforcement hooks.
  - Provide reference adapters (LangChain, n8n) and adapter acceptance tests.
- Phase 2 (scale): observability, packaging, and DX
  - Provide telemetry, policy engine, packaging (wheels, containers), and deployment guides.
  - Language Server (LSP) for editor features and diagnostics.
  - Hosted runner or deployment templates for production execution.

---

# Immediate priorities (what must be done before launch)

1. Safe evaluator
   - Replace direct eval() usage with AST-validated evaluation.
   - Whitelist a small set of operations and functions (len, basic math, comparators) and deny attribute access and arbitrary calls.
   - Add unit tests that show malicious inputs are rejected.

2. IR schema & validation
   - Add pydantic models or a JSON Schema for the compiled IR.
   - Validate IR in compile and during CI; fail builds that produce invalid IR.

3. Capability model enforcement
   - Ensure compile-time and runtime checks for capabilities.
   - Provide developer-facing diagnostics showing exactly which capability is missing and how to enable it.

4. CI baseline
   - GitHub Actions: ruff, mypy, pytest, IR schema validation.
   - Mock integrations in tests; never call live endpoints in CI.

---

# Medium-term work (stability & DX)

- Grammar-based parser (Lark)
  - Produce AST nodes with (line, col) metadata for reliable diagnostics and tooling.
  - Provide a compatibility migration guide for existing .apl samples.

- ToolProxy & Adapters SDK
  - Define a minimal adapter interface (register, declare capabilities, call) and example adapters.
  - Ship adapter acceptance tests that run against mocked services.

- Observability & Governance
  - Structured logs, traces, and provenance metadata embedded in IR and runtime outputs.
  - Policy engine: deny/allow side-effects in configurable environments.

- Packaging & Deployment
  - Releaseable wheel artifacts for compiler and runtime.
  - Docker images for a recommended hosted runner pattern and k8s deployment templates.

---

# Long-term goals (platform & ecosystem)

- LSP and editor integrations (syntax, completions, in-line diagnostics).
- Backwards-compatibility and migration tooling for IR versions.
- Marketplace / registry patterns for adapters, tool proxies, and shared capability manifests.
- Optional hosted offering with secure execution, RBAC, and audit trails.

---

# Success metrics (measurable)

First 90 days
- CI green for all PRs and test coverage ≥ 80% for core modules.
- No high/critical security findings in runtime eval.
- Two working adapters (LangChain + n8n) with end-to-end example runs.
- Author → compile → run tutorial completed by an engineer in ≤ 30 minutes.

Next 6 months
- Multiple active adapters maintained by community or partners.
- Stable IR versioning with a deprecation policy.
- Adoption in 2+ internal projects.

---

# Recommended first PRs (ordered, small → medium)

1. Safe-eval implementation for runtime._eval_expr and _eval_kwargs (3–8 hours).
2. IR pydantic models + validator and unit tests (3–6 hours).
3. GitHub Actions workflow: lint/type/tests/schema checks (1–2 hours).
4. Parser test-suite for edge cases & ambiguous input (2–6 hours).
5. ToolProxy interface and one small adapter using mocked external service (2–3 days).

---

# Security & governance notes

- Runtime must default to sandboxed behavior: no storage/network/exec without explicit capability declaration and runtime flag.
- All adapters run in a permissioned context; capability manifests must be explicit and auditable.
- Provide SECURITY.md and runtime security documentation that explains threat model and mitigation steps.

---

# How to incorporate these principles into documentation

- Add the "Launch & Scale Strategy" section to README.md and PRD.md as a concise summary.
- Add a SECURITY.md describing the runtime threat model and safe deployment guidance.
- Keep DESIGN_PRINCIPLES.md as the canonical source for architecture and link to targeted docs (IR schema, adapter SDK, LSP).
- Update CHANGELOG.md for breaking changes and migration notes.

---

# Contributor guidance (quick checklist for PRs implementing strategy items)

- Add unit tests for new behavior; coverage for critical path ≥ 80%.
- If you modify runtime eval or parser: include migration notes in PRD.md and CHANGELOG.md.
- Include example .apl showing new language features or capability declarations.
- Ensure CI verifies IR schema and adapter acceptance tests against mocks.

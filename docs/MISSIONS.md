# Missions

## Mission 1 — Minimal Agent Path
- **Objective**: Deliver a <40 LOC reference agent that validates → lints → compiles → packages → deploys with deterministic output.
- **KPIs**: Setup time ≤15 minutes; 5 command workflow documented in README; smoke tests pass across local and container targets.
- **Owners**: Language + Runtime team.
- **Dependencies**: ToolRegistry, safe evaluators, container packaging.

## Mission 2 — Structured Tooling & MCP Discovery
- **Objective**: Replace heuristic dotted-call handling with a ToolRegistry + MCP resolver that manages discovery, authentication, and invocation.
- **KPIs**: 100% of `binds` resolved or rejected at compile time; >=90% test coverage on registry/proxy modules; zero `eval` usage in dispatch path.
- **Owners**: Integrations team.
- **Dependencies**: CapabilityManager, registry fixtures, adapter plugin API.

## Mission 3 — Safety & Capability Enforcement
- **Objective**: Enforce capability manifests end-to-end with runtime gating, audit logs, and threat modeling.
- **KPIs**: Automated tests fail on unauthorized capability usage; audit logs include tool, capability, and arguments; PRD threat model appendix updated.
- **Owners**: Security & Runtime team.
- **Dependencies**: ToolRegistry telemetry hooks, safe evaluator, CI policy checks.

## Mission 4 — Developer Experience & IDE Support
- **Objective**: Ship IDE tooling (VS Code extension, Tree-sitter grammar) and align repository workflows with `ruff`/`mypy`/`pytest`.
- **KPIs**: `.apl` syntax highlighting available in VS Code marketplace; lint/type/test run automatically in CI; contributor satisfaction survey ≥4/5.
- **Owners**: DX team.
- **Dependencies**: Grammar specification, CLI telemetry, documentation updates.

## Mission 5 — Production-Ready Deployment
- **Objective**: Package agents into wheels, containers, and serverless bundles with automated smoke tests.
- **KPIs**: At least one example deployed to Docker and AWS Lambda with reproducible instructions; automated smoke tests cover packaging outputs; runtime telemetry exported for deployments.
- **Owners**: Platform team.
- **Dependencies**: Packaging pipeline, capability manifests, observability hooks.

# Roadmap

> Updated: 2025-11-09. Owners must refresh dates and status every sprint.

## Now — Sprint 0 (Nov 10–Nov 24, 2025)
- **Goals**
  - Land `ToolRegistry` plumbing and replace dotted-call heuristics in `Runtime.execute_step`.
  - Introduce safe literal evaluator for expressions/kwargs and integrate `CapabilityManager`.
  - Document minimal agent workflow (<40 LOC) in README + examples.
- **Deliverables**
  - `packages/python/src/apl/tools.py` (ToolRegistry, ToolProxy) with ≥90% unit test coverage.
  - Updated runtime dispatch pipeline calling proxies and logging capability usage.
  - Regression tests for bind resolution + mock MCP registry fixtures.
  - Updated docs: `PRD.md`, `MISSION.md`, `SETUP_RULES.md`, `examples/minimal_agent.apl`.
- **Exit Criteria**
  - `python -m apl run examples/minimal_agent.apl` produces deterministic output with tool dispatch path exercised.
  - CI runs `ruff`, `mypy`, `pytest` cleanly.
  - `ROADMAP.md` status reviewed in weekly stand-up.

## Next — Sprint 1 (Nov 25–Dec 16, 2025)
- **Goals**
  - Implement MCP registry client + proxy stack with caching and env overrides.
  - Ship CapabilityManager enforcement with audit logging and threat model appendix.
  - Provide interim VS Code syntax highlighting + lint integration guidance.
- **Deliverables**
  - `packages/python/src/apl/mcp.py` with registry fetch, schema validation, and proxy factory.
  - Capability manifest schema + runtime enforcement tests.
  - Temporary VS Code settings snippet, Tree-sitter grammar draft, and DX instructions.
  - Example pipelines for containerized runtime (Dockerfile + smoke test).
- **Exit Criteria**
  - `apl compile` fails fast when a bind cannot be resolved; errors include remediation steps.
  - Audit log records capability, tool, args, and result for every step.
  - `.apl` files render with syntax highlighting in VS Code via extension or settings snippet.

## Later — Sprint 2 (Jan 06–Jan 31, 2026)
- **Goals**
  - Finish adapter plugin API and migrate existing integrations (Slack, n8n) to plugins.
  - Publish VS Code extension (marketplace) and Tree-sitter grammar for community editors.
  - Harden packaging/deployment path with container + serverless bundles.
- **Deliverables**
  - Plugin registration API with example adapters and documentation.
  - VS Code extension repository + release, Tree-sitter grammar tests.
  - Automated smoke tests for Docker image and AWS Lambda package.
- **Exit Criteria**
  - Adapter plugins load dynamically without modifying runtime core.
  - `.apl` syntax highlighting installed via marketplace extension.
  - Container + Lambda smoke tests run in CI with recorded logs.

## Horizon — v0.3 (Feb–Mar 2026)
- **Goals**
  - Formalize static type/effect checker and publish language server plan.
  - Deliver production deployment playbook (observability, rollback, capability audits).
  - Begin TypeScript runtime feasibility study.
- **Deliverables**
  - Type/effect checker RFC + prototype.
  - Observability guides with trace export examples.
  - Feasibility report on TS runtime with spike code.
- **Exit Criteria**
  - Type checker rejects unsafe capability flow in sample agents.
  - Ops runbook includes deployment + rollback script, monitoring dashboards.
  - Decision made (go/no-go) on TypeScript runtime timeline.

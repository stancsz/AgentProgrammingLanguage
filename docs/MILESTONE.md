# Milestones

## Milestone A — ToolRegistry & Safe Dispatch (Sprint 0)
- **Scope**
  - Add `ToolRegistry`/`ToolProxy` abstractions and integrate them into `Runtime.execute_step`.
  - Replace dotted-call JSON stub with structured tool invocation + telemetry.
  - Introduce safe literal evaluator for expressions/kwargs and remove `eval` usage.
- **Acceptance Tests**
  - `pytest tests/test_tools_registry.py` covers register/get/list/invoke paths with ≥90% branch coverage.
  - Runtime dispatch integration test invokes a fake proxy and records capability usage.
  - Lint/type/test loop (`ruff`, `mypy`, `pytest`) succeeds in CI.
- **Artifacts**
  - Updated `PRD.md` sections 1.3 and 4 referencing ToolRegistry progress.
  - Changelog entry summarizing the change set.

## Milestone B — MCP Resolver & Capability Manager (Sprint 1)
- **Scope**
  - Implement MCP registry client + proxy creation with cache + env override support.
  - Build `CapabilityManager` enforcing manifests at runtime and logging violations.
  - Extend CLI to fail fast on unresolved binds or unauthorized capabilities.
- **Acceptance Tests**
  - `pytest tests/test_mcp_resolver.py` verifying registry fetch, schema validation, and proxy wiring.
  - Runtime tests covering capability allow/deny scenarios with deterministic error messages.
  - Threat model appendix added to `PRD.md`.
- **Artifacts**
  - Updated docs (`SETUP_RULES.md`, `ROADMAP.md`) reflecting new workflow.
  - Example `.apl` showcasing MCP bind resolution.

## Milestone C — IDE & Developer Experience (Sprint 1 overlap)
- **Scope**
  - Publish interim VS Code extension or settings snippet for `.apl` syntax highlighting.
  - Integrate `ruff`/`mypy` checks into developer onboarding and CI templates.
  - Document end-to-end workflow (<40 LOC) in README + examples.
- **Acceptance Tests**
  - VS Code extension renders syntax highlight + snippets; manual QA recorded.
  - `SETUP_RULES.md` instructions verified by onboarding walkthrough; new hire able to run minimal agent in ≤15 minutes.
  - CI gating on `ruff`/`mypy`/`pytest`.
- **Artifacts**
  - Screenshots or screencast of IDE support committed under `docs/`.
  - Updated README quickstart reflecting minimal workflow.

## Milestone D — Deployment Playbook (Sprint 2)
- **Scope**
  - Package agents into wheel, Docker image, and AWS Lambda zip with reproducible scripts.
  - Add smoke tests and observability hooks to verify runtime behavior post-deploy.
  - Provide rollback guidance and capability audit checklist.
- **Acceptance Tests**
  - `scripts/smoke/docker_smoke.sh` and `scripts/smoke/lambda_smoke.py` pass in CI.
  - Deployment logs include tool/capability traces and are linked in documentation.
  - Rollback playbook executed during review (tabletop exercise).
- **Artifacts**
  - Deployment guide under `docs/deployment.md`.
  - Recorded smoke test outputs attached to release notes.

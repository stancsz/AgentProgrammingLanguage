# Developer Guidelines

## Contribution Flow
1. Pick or create a GitHub issue and align it with the roadmap milestone.
2. Branch from `main` using `feature/<issue-id>-short-description`.
3. Follow the workflow in `SETUP_RULES.md` (venv → install deps → lint/type/test).
4. Open a draft PR early, link Issue #16 or subsequent roadmap issues, and keep the checklist updated.

## Coding Standards
- Maintain Python-aligned syntax for `.apl` constructs—if `ruff` flags it, fix it.
- Avoid dynamic `eval`/`exec`; use the safe evaluators in the runtime.
- Keep functions small, deterministic, and covered by tests. Document complex control flow with short comments (no noise).
- Place integration adapters behind `ToolProxy` abstractions instead of hardcoding runtime branches.

## Testing Requirements
- Unit tests for parser, runtime, registry, and capability enforcement are mandatory for new behavior.
- Integration tests must cover the minimal agent deployment path (<40 LOC).
- Mock external services (MCP, Slack, n8n) using fixtures—never hit live endpoints in CI.
- Keep coverage trend ≥80% for `packages/python/src/apl`.

## Documentation
- Update `PRD.md`, `MISSION.md`, `DESIGN_PRINCIPLES.md`, `ROADMAP.md`, and `MILESTONE.md` when behavior, priorities, or timelines shift.
- Add or refresh example `.apl` programs to showcase new language features.
- Record migration notes for breaking changes in `CHANGELOG.md` (add the file if missing).

## Code Review Expectations
- Every PR must include: summary, testing evidence (`ruff`, `mypy`, `pytest` outputs), screenshots or logs for runtime changes.
- Reviewers block on missing tests, unsafe evaluation, undocumented capability usage, or roadmap misalignment.
- Keep PRs focused (≤500 lines diff when possible); split feature work into reviewable steps.

## Release & Deployment
- Tag milestones with semantic versions (`v0.x.y`) once `MILESTONE.md` acceptance criteria are met.
- Build and publish wheels/containers using the `python -m apl compile` pipeline before releasing.
- Maintain reproducible release notes referencing mission/roadmap alignment and regression test results.

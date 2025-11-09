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

# Mission

## North Star
Build the Agent Programming Language (APL) into the fastest way to define, test, and deploy production agents. Teams should move from idea to a running agent in fewer than 40 lines of code and five terminal commands while inheriting Python’s tooling, safety posture, and deployment story.

## Problem We Solve
- Hand-authored prompt chains are brittle, opaque, and hard to audit.
- Existing orchestration frameworks require bespoke Python glue with ad-hoc capability checking.
- Tool and MCP integration is fragmented, making agent behaviors hard to reproduce across environments.

## Our Approach
- **Python-aligned DSL**: Keep the surface syntax close to Python so existing linting, typing, and formatting workflows apply out of the box.
- **Structured runtime**: Own tool discovery, capability enforcement, and replayable execution so agents behave deterministically in local, container, and serverless contexts.
- **Developer-first ergonomics**: Offer CLI, IDE extensions, and documentation that make authoring agents feel like building a modern Python service.

## Success Measures
- <40 LOC reference agent that validates → lints (ruff) → compiles → packages → deploys in 5 steps.
- 100% of declared `binds` resolved through the ToolRegistry or rejected with actionable diagnostics.
- Capability violations prevented at runtime, with regression tests covering the full dispatch path.
- `.apl` files highlighted and linted in VS Code and at least one alternative IDE.

## Constraints & Non-Goals
- APL will not duplicate general-purpose Python features (loop semantics, package resolution) beyond what is required for deterministic agent execution.
- We will not own commercial MCP hosting; APL integrates with existing registries and connectors.
- Native runtimes beyond Python are deferred until the Python stack reaches Milestone “Battle-tested Runtime”.

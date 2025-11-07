# Agent Programming Language - Grammar & Quick Reference

Purpose
- A loose, human-first programming language for describing agent workflows.
- Designed for easy authoring; translator targets a LangGraph-compatible IR and a reference runtime.
- Default: nondestructive; IO/network actions require explicit capability flags.

Design principles
- Keep syntax informal but structured: keywords are lightweight; most lines are "steps".
- Allow free-form text in prompts and comments.
- Provide minimal formal constructs (tasks, steps, vars, control flow, assertions) to enable deterministic translation.

Top-level structure
- program <name> [meta]
- task <name>(arg1, arg2, ...)
- step <assignment?> = <action>(...)
- precondition: <expression>
- postcondition: <expression>
- requires capability.<name>
- end

Whitespace and comments
- Lines starting with `#` are comments.
- Indentation is optional; blocks are delimited by `task` ... `end`.

Primitive actions (examples)
- call_llm(model="gpt-4", prompt="...")
- fetch(url)
- compute(expr)
- store(destination, value)
- assert <expression>

Expressions
- Use Python-like expressions for simplicity (len(x), x == "", "substr" in s, etc.).
- Variables are referenced by name: {{var}} may appear inside string prompts for templating.

Example APL program
```apl
program demo_store(version="0.1")

task summarize_and_store(url)
  precondition: url != ""
  step raw = fetch(url)
  step summary = call_llm(model="mock", prompt="Summarize: {{raw}}")
  step assert len(summary) > 0
  step store("local://data/summary.txt", summary) requires capability.storage
end
```

LangGraph translation overview
- Each task -> LangGraph "subgraph" / node group.
- Each step -> LangGraph node with:
  - id: generated unique id
  - kind: primitive name (call_llm, fetch, compute, store, assert)
  - inputs: variable references or literals
  - outputs: variable name (if assigned)
  - metadata: capabilities, retries, source line

Example LangGraph-like node (illustrative)
```json
{
  "nodes": [
    {
      "id": "n1",
      "kind": "fetch",
      "inputs": { "url": "http://..." },
      "outputs": ["raw"]
    },
    {
      "id": "n2",
      "kind": "call_llm",
      "inputs": { "model": "mock", "prompt": "Summarize: {{raw}}" },
      "outputs": ["summary"]
    },
    {
      "id": "n3",
      "kind": "assert",
      "inputs": { "expr": "len(summary) > 0" }
    }
  ],
  "edges": [
    ["n1", "n2"],
    ["n2", "n3"]
  ]
}
```

Translation guidelines
- Templated prompts: replace {{var}} with node output references in LangGraph inputs.
- Control flow: translate simple if/for into conditional nodes or subgraphs; complex flow can be flattened with guard nodes.
- Capabilities: attach capability tags to nodes; runtime enforces them.

Ambiguity & fallbacks
- If parsing ambiguity occurs, translator emits a warning and inserts an explicit "verify" node requiring human review.
- For highly free-form lines not matching primitives, create a `call_llm` node with the line as prompt (fallback).

Next steps (implementation-focused)
- Produce a formal set of parser tests that reflect this loose syntax.
- Implement translator mapping rules to a LangGraph JSON schema.
- Provide mock LLM primitive and capability enforcement in the runtime.

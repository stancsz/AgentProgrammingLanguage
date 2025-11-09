# Agent Programming Language (APL) - README

A statically-typed Domain-Specific Language (DSL) for agent engineering that compiles (or transpiles) to Python.

APL is a lightweight, AI-native agent programming language that lets intent be expressed once and re-used across runtimes. It provides a simple surface that AI systems, human operators, and non-developers can read, reproduce, and test. The compiler emits Python and a portable IR and can target orchestration frameworks (LangChain, LlamaIndex, AutoGen, LangGraph) and integrate MCP tool adapters to keep agent code portable.

## Example — Customer support: pseudo → APL → compile → framework adapter

This project uses a single focused example to demonstrate the end-to-end flow: from pseudo-spec to APL source, compile to Python + IR, and a conceptual framework adapter mapping. The example lives at examples/customer_support.apl and matches the APL shown below.

1) Pseudo-spec (customer support)
```text
Customer: "My billing page shows an error and my invoice is missing."
Goal: create a service-desk ticket, attach account data, schedule a follow-up with an account manager, and reply to the customer.
Requirements: use MCP service-desk and CRM tools; declare network and storage capabilities.
```

2) APL source (examples/customer_support.apl)
```apl
program customer_support_demo(version="0.1")

agent support_agent binds mcp.servicedesk as sd, mcp.crm as crm:
  capability network
  capability storage
  capability call_llm

  def handle_request(customer_id, message):
    precondition: message != ""
    step account = crm.get_account(id=customer_id) requires capability.network
    step ticket = sd.create_ticket(
      title="Support request from {{account.name}}",
      body=message,
      customer_id=customer_id
    ) requires capability.network
    step store_result = store("local://tickets/{{ticket.id}}.txt", "Ticket created: {{ticket.id}}") requires capability.storage
    step am = crm.assign_account_manager(account_id=account.id) requires capability.network
    step followup_date = crm.schedule_followup(account_id=account.id, days=3) requires capability.network
    step prompt = "Draft a friendly reply to the customer summarizing the ticket {{ticket.id}} and scheduled follow-up on {{followup_date}}."
    step reply = call_llm(model="gpt-5-mini", prompt=prompt) requires capability.call_llm
    return { "ticket_id": ticket.id, "reply": reply, "followup_date": followup_date, "assigned_manager": am }
end
```

3) Compile to Python + IR (reference compiler)
```bash
python -m apl compile examples/customer_support.apl --python-out dist/customer_support.py --ir-out dist/customer_support.json
```

4) Conceptual LangChain adapter (minimal)
```python
# conceptual mapping: IR -> PromptTemplate / LLMChain
import json
from langchain import PromptTemplate, LLMChain
from langchain.llms import OpenAI

ir = json.load(open("dist/customer_support.json"))
# pick call_llm nodes and construct prompt templates
llm_nodes = [n for n in ir["nodes"] if n["kind"] == "call_llm"]
for node in llm_nodes:
    template = node["input"]            # APL uses {{var}} templating
    prompt = PromptTemplate(template=template, input_variables=["followup_date"])
    llm = OpenAI(model_name="gpt-5-mini")
    chain = LLMChain(llm=llm, prompt=prompt)
    out = chain.run(followup_date="2025-11-12")
    print(out)
```

5) Adapter mapping notes (MCP/tool calls, AutoGen, LangGraph)
- MCP tool nodes (e.g., `crm.get_account`, `sd.create_ticket`) map to framework "tools" or SDK calls. Adapters should register tool wrappers that enforce required capabilities and translate arguments.
- Use `ir["edges"]` to wire dataflow between nodes; map node inputs/outputs to framework variables or chain inputs.
- AutoGen mapping: translate APL tasks/subgraphs to agent/task specs and wire tool adapters as tools available to agents.
- LangGraph: emit or translate APL IR to a LangGraph-compatible schema for visualization and orchestration.

Notes
- The IR (dist/*.json) contains capability manifests and an `ir_hash` for provenance; adapters must validate provenance and required capabilities before execution.
- Keep python: escape hatches gated by explicit capabilities so adapters can refuse or require manual approval.

## Key capabilities
- Turn natural or pseudo-code agent descriptions into validated APL source and portable IR; map IR to framework artifacts to speed agentic development and reuse.

## Goals
- Define a Python-aligned agent language with formal grammar, static capability typing, and deterministic semantics.
- Deliver a reference compiler pipeline and runtime that make APL programs executable, observable, and safe by default.
- Supply tooling—CLI, tests, CI workflows, documentation—that enables teams to author, validate, package, and ship production-grade agent code.

## Language foundations
- Python-aligned surface syntax, first-class agent module system, static capability typing, deterministic compilation pipeline, and runtime contracts.

## Contact / Contributing
Follow standard PR process. Update PRD.md when changing language semantics.

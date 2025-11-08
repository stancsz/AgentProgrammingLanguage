# Lead qualification agent that scores inbound leads and notifies sales.

agent lead_qualification binds mcp.crm as crm, mcp.slack as slack:
  # n8n: trigger webhook path="/hooks/leads" method="POST"
  def score(lead):
    summary = call_llm(model="sales", prompt="Summarize company and ask qualification questions: {{lead}}")
    score = call_llm(model="sales", prompt="Score lead (0-100) based on: {{lead}}")
    crm.update_lead(id="auto", score=score, notes=summary)
    slack.post(channel="#sales", text=f"Lead scored {score}")
    return {"score": score, "notes": summary}

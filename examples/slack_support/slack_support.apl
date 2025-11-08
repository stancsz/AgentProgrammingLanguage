# Slack support agent that triages inbound tickets and posts updates.

agent slack_support binds mcp.slack as slack, mcp.kb as knowledge:
  # n8n: trigger webhook path="/hooks/slack/support" method="POST"
  def triage(ticket):
    ticket_summary = call_llm(model="support", prompt="Summarize support ticket: {{ticket}}")
    resolution = call_llm(model="support", prompt="Draft helpful reply for: {{ticket}}")
    slack.post(channel="#support", text=resolution)
    knowledge.append(article=ticket_summary)
    return {"summary": ticket_summary, "reply": resolution}

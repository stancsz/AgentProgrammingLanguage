# Email/CRM customer support escalation agent.

agent customer_support binds mcp.email as email, mcp.crm as crm:
  # n8n: trigger webhook path="/hooks/email/support" method="POST"
  def escalate(message):
    intent = call_llm(model="support", prompt="Classify support intent: {{message}}")
    priority = call_llm(model="support", prompt="Assign priority (low/medium/high) for: {{message}}")
    crm.create_case(intent=intent, priority=priority, description=message) requires capability.crm
    email.send(to="support-team@example.com", subject="New support case", body=message) requires capability.email
    return {"intent": intent, "priority": priority}

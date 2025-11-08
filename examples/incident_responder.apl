# Operational incident responder agent connecting Slack and PagerDuty.

agent incident_responder binds mcp.pagerduty as pagerduty, mcp.slack as slack:
  # n8n: trigger webhook path="/hooks/incidents" method="POST"
  def handle(alert):
    severity = call_llm(model="ops", prompt="Classify severity (sev1-sev3) for alert: {{alert}}")
    playbook = call_llm(model="ops", prompt="Select playbook for alert: {{alert}}")
    slack.post(channel="#incident-room", text=f"New {severity} incident. Playbook: {playbook}")
    pagerduty.trigger(severity=severity, details=alert) requires capability.pagerduty
    return {"severity": severity, "playbook": playbook}

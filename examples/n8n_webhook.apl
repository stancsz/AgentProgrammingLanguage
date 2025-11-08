# n8n annotated agent demonstrating webhook trigger and workflow handoff

agent notifier:
  # n8n: trigger webhook path="/apl/notifier" method="POST"
  def run(payload):
    status = n8n.workflow(workflow_id="slack-notify", payload=payload)
    return status

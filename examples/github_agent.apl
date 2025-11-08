# GitHub backlog grooming agent.

agent github_agent binds mcp.github as gh, mcp.issue_tracker as tracker:
  def groom(issue):
    labels = call_llm(model="product", prompt="Suggest GitHub labels for issue: {{issue}}")
    summary = call_llm(model="product", prompt="Summarize the issue in one sentence: {{issue}}")
    gh.update_issue(labels=labels.split(","), summary=summary)
    tracker.record(issue=summary, labels=labels)
    return {"labels": labels, "summary": summary}

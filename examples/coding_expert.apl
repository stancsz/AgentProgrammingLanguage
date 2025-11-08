# Coding expert agent focused on code review triage.

agent coding_expert binds mcp.github as gh, mcp.slack as slack:
  def review(patch):
    findings = call_llm(model="code-reviewer", prompt="Review the following diff and enumerate issues: {{patch}}")
    tests = call_llm(model="code-reviewer", prompt="Suggest regression tests for: {{patch}}")
    slack.post(channel="#engineering", text=findings)
    gh.comment(pr="auto", body=findings)
    return {"findings": findings, "tests": tests}

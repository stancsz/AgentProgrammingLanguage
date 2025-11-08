# Release briefing agent that compiles notes and posts updates.

agent release_brief binds mcp.github as gh, mcp.slack as slack:
  def publish(repo, tag):
    commits = gh.list_commits(repo=repo, tag=tag)
    changelog = call_llm(model="writer", prompt="Draft release notes:\nCommits: {{commits}}")
    slack.post(channel="#release", text=changelog)
    gh.create_release(repo=repo, tag=tag, notes=changelog)
    return changelog

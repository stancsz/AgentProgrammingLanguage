# Requires a running Slack MCP server (https://modelcontextprotocol.io/registry).
program slack_support_test(version="0.1")

agent slack_post_message binds mcp.slack as slack:
  def send():
    slack.post(channel="env:SLACK_CHANNEL_ID", text="APL Slack support smoke test via apl run")

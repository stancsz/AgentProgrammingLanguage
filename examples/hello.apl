# Example programs for Agent Programming Language (APL)
# Demonstrates Python-like agent defs, MCP bindings, sub-agents, and simple flows.

agent hello_world:
  def greet(name):
    # simple LLM greeting (mockable)
    msg = call_llm(model="mock", prompt=f"Say hello to {name}")
    assert "hello" in msg.lower()
    return msg

agent data_agent(name) binds mcp.newsapi as news, mcp.storage as s3:
  def run(query):
    # MCP tool call (news.search) and LLM summarization
    articles = news.search(query)
    summary = call_llm(model="mock", prompt=f"Summarize: {articles}")
    s3.put(f"bucket/{name}/summary.txt", summary) requires capability.storage
    return summary

agent orchestrator:
  def main():
    scraper = data_agent("scraper")         # compose sub-agent
    result = scraper.run("latest AI news") # agent-to-agent call
    notify = call_llm(model="mock", prompt=f"Notify: {result}")
    return notify

# Loose-fallback example: free-form prompt line becomes call_llm fallback
agent loose_example:
  "Search latest research and summarise for me"

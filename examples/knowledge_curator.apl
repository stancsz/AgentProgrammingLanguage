# Knowledge curator agent that collects search results and synthesizes summaries.

agent knowledge_curator binds mcp.search as search, mcp.kb as knowledge:
  def ingest(query):
    results = search.fetch(query=query, limit=5)
    synthesis = call_llm(model="researcher", prompt="Synthesize key facts:\n{{results}}")
    knowledge.append(summary=synthesis)
    return synthesis

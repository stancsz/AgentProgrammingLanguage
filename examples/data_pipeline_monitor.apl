# Data pipeline monitor agent that summarizes telemetry.

agent data_pipeline_monitor binds mcp.metrics as metrics, mcp.slack as slack:
  def check(job_name):
    stats = metrics.fetch(job=job_name)
    health = call_llm(model="ops", prompt="Derive health summary for job metrics: {{stats}}")
    slack.post(channel="#data-operations", text=f"Health report for {job_name}: {health}")
    return health

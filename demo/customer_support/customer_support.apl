program customer_support_demo(version="0.1")

agent support_agent binds mcp.servicedesk as sd, mcp.crm as crm:
  capability network
  capability storage
  capability call_llm

  def handle_request(customer_id, message):
    precondition: message != ""
    step account = crm.get_account(id=customer_id) requires capability.network
    step ticket = sd.create_ticket(
      title="Support request from {{account.name}}",
      body=message,
      customer_id=customer_id
    ) requires capability.network
    step store_result = store("local://tickets/{{ticket.id}}.txt", "Ticket created: {{ticket.id}}") requires capability.storage
    step am = crm.assign_account_manager(account_id=account.id) requires capability.network
    step followup_date = crm.schedule_followup(account_id=account.id, days=3) requires capability.network
    step prompt = "Draft a friendly reply to the customer summarizing the ticket {{ticket.id}} and scheduled follow-up on {{followup_date}}."
    step reply = call_llm(model="gpt-5-mini", prompt=prompt) requires capability.call_llm
    return { "ticket_id": ticket.id, "reply": reply, "followup_date": followup_date, "assigned_manager": am }
end

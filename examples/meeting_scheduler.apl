# Meeting scheduler agent coordinating calendar holds and email follow-up.

agent meeting_scheduler binds mcp.calendar as calendar, mcp.email as email:
  def arrange(request):
    availability = calendar.find_slots(participants="team")
    proposal = call_llm(model="assistant", prompt="Draft scheduling email using slots: {{availability}} and request: {{request}}")
    email.send(to="organizer@example.com", subject="Meeting proposal", body=proposal) requires capability.email
    calendar.hold(slot="next_available", participants="team")
    return {"slots": availability, "message": proposal}

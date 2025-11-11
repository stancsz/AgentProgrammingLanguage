"""Compiled APL program (auto-generated)."""

from apl.ast import Program, Task, Step
from apl.runtime import Runtime

PROGRAM = Program(
    name='customer_support_demo',
    meta={'version': '0.1', 'agents': {'support_agent': {'args': [], 'binds': {'sd': 'mcp.servicedesk', 'crm': 'mcp.crm'}, 'capabilities': ['network', 'storage', 'call_llm']}}},
    tasks=[
    Task(
        name='support_agent.handle_request',
        args=['customer_id', 'message'],
        precondition='message != ""',
        postcondition=None,
        steps=[
            Step(
                raw='step account = crm.get_account(id=customer_id) requires capability.network',
                assignment='account',
                action='crm.get_account',
                args='id=customer_id',
                requires=['network'],
            ),
            Step(
                raw='step ticket = sd.create_ticket(',
                assignment='ticket',
                action=None,
                args='sd.create_ticket(',
                requires=[],
            ),
            Step(
                raw='title="Support request from {{account.name}}",',
                assignment='title',
                action=None,
                args='"Support request from {{account.name}}",',
                requires=[],
            ),
            Step(
                raw='body=message,',
                assignment='body',
                action=None,
                args='message,',
                requires=[],
            ),
            Step(
                raw='customer_id=customer_id',
                assignment='customer_id',
                action=None,
                args='customer_id',
                requires=[],
            ),
            Step(
                raw=') requires capability.network',
                assignment=None,
                action=None,
                args=')',
                requires=['network'],
            ),
            Step(
                raw='step store_result = store("local://tickets/{{ticket.id}}.txt", "Ticket created: {{ticket.id}}") requires capability.storage',
                assignment='store_result',
                action='store',
                args='"local://tickets/{{ticket.id}}.txt", "Ticket created: {{ticket.id}}"',
                requires=['storage'],
            ),
            Step(
                raw='step am = crm.assign_account_manager(account_id=account.id) requires capability.network',
                assignment='am',
                action='crm.assign_account_manager',
                args='account_id=account.id',
                requires=['network'],
            ),
            Step(
                raw='step followup_date = crm.schedule_followup(account_id=account.id, days=3) requires capability.network',
                assignment='followup_date',
                action='crm.schedule_followup',
                args='account_id=account.id, days=3',
                requires=['network'],
            ),
            Step(
                raw='step prompt = "Draft a friendly reply to the customer summarizing the ticket {{ticket.id}} and scheduled follow-up on {{followup_date}}."',
                assignment='prompt',
                action=None,
                args='"Draft a friendly reply to the customer summarizing the ticket {{ticket.id}} and scheduled follow-up on {{followup_date}}."',
                requires=[],
            ),
            Step(
                raw='step reply = call_llm(model="gpt-5-mini", prompt=prompt) requires capability.call_llm',
                assignment='reply',
                action='call_llm',
                args='model="gpt-5-mini", prompt=prompt',
                requires=['call_llm'],
            ),
            Step(
                raw='return { "ticket_id": ticket.id, "reply": reply, "followup_date": followup_date, "assigned_manager": am }',
                assignment=None,
                action=None,
                args='return { "ticket_id": ticket.id, "reply": reply, "followup_date": followup_date, "assigned_manager": am }',
                requires=[],
            )
        ],
    )
    ],
)


def run(runtime: Runtime | None = None):
    runtime = runtime or Runtime()
    return runtime.execute_program(PROGRAM)

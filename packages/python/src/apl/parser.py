"""
APL parser module (improved scaffold)

Parses the Python-like APL agent syntax into the Program/Task/Step dataclasses
defined in packages/python/src/apl/__init__.py.

Behavior:
- Parse `program` header if present.
- Parse `agent <name> [binds ...]:` blocks.
- Parse `def <name>(args):` inside agents -> becomes a Task named "<agent>.<def>".
- Parse assignments and action calls (e.g. `x = call_llm(...)` or `items = news.search(q)`).
- Treat free-form string lines inside agent/def as call_llm fallback prompts.
- Capture `requires capability.<name>` markers on the same line.
- Store agent binds in program.meta["agents"] as { agent_name: { alias: "mcp.newsapi", ... } }

Note: This is a permissive, development-focused parser to enable examples and tests.
Replace with a full parser (lark/ANTLR) for production.
"""

from typing import Dict, Any, List, Optional
import re

# import shared AST dataclasses from package root
from . import Program, Task, Step

_agent_re = re.compile(r'^\s*agent\s+([A-Za-z0-9_]+)(?:\s*\((.*?)\))?(?:\s+binds\s+(.*?))?\s*:\s*$', re.IGNORECASE)
_def_re = re.compile(r'^\s*def\s+([A-Za-z0-9_]+)\s*\((.*?)\)\s*:\s*$', re.IGNORECASE)
_program_re = re.compile(r'^\s*program\s+([A-Za-z0-9_]+)(?:\((.*?)\))?', re.IGNORECASE)
_requires_re = re.compile(r'.*requires\s+capability\.([A-Za-z0-9_]+)', re.IGNORECASE)
_assign_call_re = re.compile(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.+)$')  # left = right
_call_re = re.compile(r'^\s*([A-Za-z0-9_.]+)\s*\((.*)\)\s*$', re.IGNORECASE)
_string_line_re = re.compile(r'^\s*["\'](.*)["\']\s*$')

def _parse_binds(binds_text: str) -> Dict[str, str]:
    """
    Parse binds like: 'mcp.newsapi as news, mcp.storage as s3'
    -> { "news": "mcp.newsapi", "s3": "mcp.storage" }
    """
    if not binds_text:
        return {}
    out = {}
    parts = [p.strip() for p in binds_text.split(',') if p.strip()]
    for p in parts:
        # expect pattern "<path> as <alias>"
        m = re.match(r'([A-Za-z0-9_.]+)\s+as\s+([A-Za-z0-9_]+)', p, re.IGNORECASE)
        if m:
            out[m.group(2)] = m.group(1)
        else:
            # fallback: treat the whole thing as a tool name mapped to itself
            key = p.split('.')[-1]
            out[key] = p
    return out

def parse_apl(text: str) -> Program:
    lines = text.splitlines()
    program_name = "__unnamed__"
    program_meta: Dict[str, Any] = {}
    program = None

    current_agent: Optional[str] = None
    current_task: Optional[Task] = None

    for raw in lines:
        ln = raw.rstrip("\n")
        s = ln.strip()
        if not s or s.startswith("#"):
            continue

        # program header
        m = _program_re.match(s)
        if m and program is None:
            program_name = m.group(1)
            meta_raw = m.group(2) or ""
            meta = {}
            for pair in re.findall(r'([A-Za-z0-9_]+)\s*=\s*"(.*?)"', meta_raw):
                meta[pair[0]] = pair[1]
            program_meta.update(meta)
            program = Program(name=program_name, meta=program_meta)
            continue

        # agent header
        m = _agent_re.match(s)
        if m:
            agent_name = m.group(1)
            agent_args = (m.group(2) or "").strip()
            binds = (m.group(3) or "").strip()
            if program is None:
                program = Program(name=program_name, meta=program_meta)
            # register agent binds in program.meta
            agents = program.meta.get("agents", {})
            agents[agent_name] = {
                "args": [a.strip() for a in agent_args.split(',') if a.strip()],
                "binds": _parse_binds(binds)
            }
            program.meta["agents"] = agents
            current_agent = agent_name
            current_task = None
            continue

        # def inside agent -> becomes a Task named "<agent>.<def>"
        m = _def_re.match(s)
        if m and current_agent:
            def_name = m.group(1)
            argstr = m.group(2) or ""
            args = [a.strip() for a in argstr.split(',') if a.strip()]
            task_name = f"{current_agent}.{def_name}"
            task = Task(name=task_name, args=args)
            if program is None:
                program = Program(name=program_name, meta=program_meta)
            program.tasks.append(task)
            current_task = task
            continue

        # end of agent block (not strict because we use ':' delim) - treat 'end' as reset
        if s.lower() == "end":
            current_agent = None
            current_task = None
            continue

        # precondition/postcondition lines (attach to current task if present)
        if s.lower().startswith("precondition:") and current_task:
            current_task.precondition = s.split(":", 1)[1].strip()
            continue
        if s.lower().startswith("postcondition:") and current_task:
            current_task.postcondition = s.split(":", 1)[1].strip()
            continue

        # inside a def/task, parse steps and assignments
        if current_task:
            # check for explicit assignment like "x = something"
            m = _assign_call_re.match(s)
            if m:
                left = m.group(1).strip()
                right = m.group(2).strip()
            else:
                left = None
                right = s

            # detect requires capability on the same line
            reqs = []
            rq = _requires_re.search(right)
            if rq:
                reqs.append(rq.group(1))
                # remove the requires clause for action parsing
                right = re.sub(r'\s*requires\s+capability\.[A-Za-z0-9_]+', '', right, flags=re.IGNORECASE).strip()

            # if right is a function call pattern like obj.method(...) or call_llm(...)
            mcall = _call_re.match(right)
            if mcall:
                action = mcall.group(1)
                args = mcall.group(2)
            else:
                # string-literal only lines are treated as fallback prompts
                mstr = _string_line_re.match(s)
                if mstr:
                    action = "call_llm"
                    args = f'prompt="{mstr.group(1)}"'
                    left = None  # fallback prompts typically not assigned
                else:
                    # treat as expression or inline tool call (e.g., news.search(query))
                    # use the raw right side as a fallback action
                    action = None
                    args = right

            step = Step(raw=s, assignment=left, action=action, args=args, requires=reqs)
            current_task.steps.append(step)
            continue

        # global-level fallback: create a top-level task "main" if not present and add step
        if program is None:
            program = Program(name=program_name, meta=program_meta)
        # ensure a main task exists
        main_task = None
        for t in program.tasks:
            if t.name == "main":
                main_task = t
                break
        if main_task is None:
            main_task = Task(name="main", args=[])
            program.tasks.append(main_task)
        # treat line as a step in main
        mstr = _string_line_re.match(s)
        if mstr:
            step = Step(raw=s, assignment=None, action="call_llm", args=f'prompt="{mstr.group(1)}"')
        else:
            step = Step(raw=s, assignment=None, action=None, args=s)
        main_task.steps.append(step)

    if program is None:
        program = Program(name=program_name, meta=program_meta)
    return program

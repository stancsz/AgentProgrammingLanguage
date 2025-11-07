"""
Agent Programming Language - minimal reference runtime & CLI scaffold.

Provides:
- simple parse_apl(text) -> AST (very permissive agent-language-friendly)
- translate_to_langgraph(ast) -> JSON-serializable dict
- MockLLM and Runtime for mock execution
- CLI: validate, translate, run --mock

This is an initial scaffold intended for development and testing; replace components as the project evolves.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import argparse
import re
import uuid
import sys

__version__ = "0.1.0"


@dataclass
class Step:
    raw: str
    assignment: Optional[str] = None
    action: Optional[str] = None
    args: Optional[str] = None
    requires: List[str] = field(default_factory=list)


@dataclass
class Task:
    name: str
    args: List[str]
    precondition: Optional[str] = None
    postcondition: Optional[str] = None
    steps: List[Step] = field(default_factory=list)


@dataclass
class Program:
    name: str
    meta: Dict[str, Any] = field(default_factory=dict)
    tasks: List[Task] = field(default_factory=list)


# --- Very small, permissive parser for the lightweight agent syntax ---
_prog_re = re.compile(r'^\s*program\s+([A-Za-z0-9_]+)(?:\((.*?)\))?', re.IGNORECASE)
_task_re = re.compile(r'^\s*task\s+([A-Za-z0-9_]+)\s*\((.*?)\)\s*', re.IGNORECASE)
_step_re = re.compile(r'^\s*step\s+(.*)', re.IGNORECASE)
_pre_re = re.compile(r'^\s*precondition\s*:\s*(.*)', re.IGNORECASE)
_post_re = re.compile(r'^\s*postcondition\s*:\s*(.*)', re.IGNORECASE)
_requires_re = re.compile(r'.*requires\s+capability\.([A-Za-z0-9_]+)', re.IGNORECASE)


def parse_apl(text: str) -> Program:
    lines = text.splitlines()
    program = None
    current_task = None

    for ln in lines:
        ln = ln.strip()
        if not ln or ln.startswith('#'):
            continue
        m = _prog_re.match(ln)
        if m:
            name = m.group(1)
            meta_raw = m.group(2) or ""
            meta = {}
            # simple meta parser: k="v",...
            for pair in re.findall(r'([A-Za-z0-9_]+)\s*=\s*"(.*?)"', meta_raw):
                meta[pair[0]] = pair[1]
            program = Program(name=name, meta=meta)
            continue
        m = _task_re.match(ln)
        if m:
            tname = m.group(1)
            args_raw = m.group(2) or ""
            args = [a.strip() for a in args_raw.split(',') if a.strip()]
            current_task = Task(name=tname, args=args)
            if program is None:
                program = Program(name="__unnamed__")
            program.tasks.append(current_task)
            continue
        if ln.lower() == 'end':
            current_task = None
            continue
        m = _pre_re.match(ln)
        if m and current_task:
            current_task.precondition = m.group(1).strip()
            continue
        m = _post_re.match(ln)
        if m and current_task:
            current_task.postcondition = m.group(1).strip()
            continue
        m = _step_re.match(ln)
        if m and current_task:
            body = m.group(1).strip()
            # parse assignment: name = action(...)
            assign = None
            action = None
            args = None
            if '=' in body:
                left, right = body.split('=', 1)
                assign = left.strip()
                right = right.strip()
            else:
                right = body
            # find requires capability
            reqs = []
            rq = _requires_re.search(right)
            if rq:
                reqs.append(rq.group(1))
                # remove the requires clause text for action parsing
                right = re.sub(r'\s*requires\s+capability\.[A-Za-z0-9_]+', '', right, flags=re.IGNORECASE).strip()
            # action name and args crude parse
            m2 = re.match(r'([A-Za-z0-9_]+)\s*\((.*)\)\s*', right)
            if m2:
                action = m2.group(1)
                args = m2.group(2)
            else:
                # fallback: treat entire right side as a prompt for call_llm
                action = "call_llm"
                args = f'prompt="{right}"'
            step = Step(raw=body, assignment=assign, action=action, args=args, requires=reqs)
            current_task.steps.append(step)
            continue
        # fallback: treat any other line inside a task as a free step
        if current_task:
            step = Step(raw=ln, assignment=None, action="call_llm", args=f'prompt="{ln}"')
            current_task.steps.append(step)
    if program is None:
        return Program(name="__empty__")
    return program


# --- Translator to LangGraph-like IR (simplified) ---
def translate_to_langgraph(program: Program) -> Dict[str, Any]:
    nodes = []
    edges = []
    for task in program.tasks:
        prev_id = None
        for step in task.steps:
            nid = str(uuid.uuid4())
            node = {
                "id": nid,
                "kind": step.action,
                "input_args": step.args,
                "output": step.assignment,
                "requires": step.requires,
                "source": step.raw
            }
            nodes.append(node)
            if prev_id:
                edges.append([prev_id, nid])
            prev_id = nid
    return {"program": program.name, "nodes": nodes, "edges": edges}


# --- Mock LLM and primitive implementations (deterministic) ---
class MockLLM:
    def __init__(self, seed: str = "mock"):
        self.seed = seed

    def call(self, prompt: str, model: str = "mock"):
        # deterministic: echo prompt with prefix, trimmed
        p = prompt.strip()
        return f"[mocked:{model}] {p}"


class Runtime:
    def __init__(self, llm=None, allow_storage=False):
        self.llm = llm or MockLLM()
        self.allow_storage = allow_storage
        self.vars = {}

    def _eval_expr(self, expr: str):
        # VERY simple evaluator for TDD / prototyping: use eval with locals mapping.
        # WARNING: insecure. Replace with a proper safe evaluator before running untrusted code.
        try:
            return eval(expr, {"__builtins__": {}}, dict(self.vars))
        except Exception as e:
            raise RuntimeError(f"Expression eval error: {e}")

    def execute_program(self, program: Program):
        results = {}
        for task in program.tasks:
            if task.precondition:
                ok = self._eval_expr(task.precondition)
                if not ok:
                    raise RuntimeError(f"Precondition failed for task {task.name}: {task.precondition}")
            for step in task.steps:
                out = self.execute_step(step)
                if step.assignment:
                    self.vars[step.assignment] = out
            if task.postcondition:
                ok = self._eval_expr(task.postcondition)
                if not ok:
                    raise RuntimeError(f"Postcondition failed for task {task.name}: {task.postcondition}")
            results[task.name] = dict(self.vars)
        return results

    def execute_step(self, step: Step):
        kind = (step.action or "").lower()
        if kind == "fetch":
            # crude: extract first string literal or return url text
            arg = step.args or ""
            m = re.search(r'["\'](.*?)["\']', arg)
            url = m.group(1) if m else arg
            return f"fetched({url})"
        if kind == "call_llm":
            # extract prompt param or use args as raw prompt
            args = step.args or ""
            m = re.search(r'prompt\s*=\s*"(.*)"', args)
            prompt = m.group(1) if m else args
            # support variable templating {{var}}
            prompt = re.sub(r'\{\{([A-Za-z0-9_]+)\}\}', lambda mo: str(self.vars.get(mo.group(1), "")), prompt)
            return self.llm.call(prompt)
        if kind == "store":
            if not self.allow_storage:
                raise RuntimeError("Storage capability not enabled for runtime.")
            # naive: return success message
            return "stored"
        if kind == "assert":
            expr = step.args or ""
            ok = self._eval_expr(expr)
            if not ok:
                raise RuntimeError(f"Assertion failed: {expr}")
            return True
        # fallback: return raw step string
        return step.raw


# --- CLI ---
def _cmd_validate(args):
    text = open(args.file, 'r', encoding='utf-8').read()
    program = parse_apl(text)
    print(json.dumps({
        "program": program.name,
        "meta": program.meta,
        "tasks": [{ "name": t.name, "args": t.args, "steps": [s.raw for s in t.steps] } for t in program.tasks]
    }, indent=2))


def _cmd_translate(args):
    text = open(args.file, 'r', encoding='utf-8').read()
    program = parse_apl(text)
    lg = translate_to_langgraph(program)
    print(json.dumps(lg, indent=2))


def _cmd_run(args):
    text = open(args.file, 'r', encoding='utf-8').read()
    program = parse_apl(text)
    rt = Runtime(allow_storage=args.allow_storage)
    result = rt.execute_program(program)
    print(json.dumps(result, indent=2))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="apl", description="Agent Programming Language - CLI (scaffold)")
    sub = parser.add_subparsers(dest="cmd")
    p_val = sub.add_parser("validate", help="parse and show AST")
    p_val.add_argument("file")
    p_trans = sub.add_parser("translate", help="translate to LangGraph-like JSON")
    p_trans.add_argument("file")
    p_run = sub.add_parser("run", help="run program in mock mode")
    p_run.add_argument("file")
    p_run.add_argument("--allow-storage", dest="allow_storage", action="store_true")
    parsed = parser.parse_args(argv)
    if parsed.cmd == "validate":
        _cmd_validate(parsed)
    elif parsed.cmd == "translate":
        _cmd_translate(parsed)
    elif parsed.cmd == "run":
        _cmd_run(parsed)
    else:
        parser.print_help()


if __name__ == "__main__":
    main(sys.argv[1:])

"""
APL CLI module.

Provides a lightweight CLI that uses the parser, translator, and runtime scaffold.
Intended for development and testing.
"""

import argparse
import json
import sys
from .parser import parse_apl
from . import translate_to_langgraph, Runtime

def cmd_validate(path: str):
    text = open(path, "r", encoding="utf-8").read()
    program = parse_apl(text)
    out = {
        "program": program.name,
        "meta": program.meta,
        "tasks": [{"name": t.name, "args": t.args, "steps": [s.raw for s in t.steps]} for t in program.tasks],
    }
    print(json.dumps(out, indent=2))

def cmd_translate(path: str):
    text = open(path, "r", encoding="utf-8").read()
    program = parse_apl(text)
    lg = translate_to_langgraph(program)
    print(json.dumps(lg, indent=2))

def cmd_run(path: str, allow_storage: bool):
    text = open(path, "r", encoding="utf-8").read()
    program = parse_apl(text)
    rt = Runtime(allow_storage=allow_storage)
    result = rt.execute_program(program)
    print(json.dumps(result, indent=2))

def main(argv=None):
    parser = argparse.ArgumentParser(prog="apl", description="Agent Programming Language CLI")
    sub = parser.add_subparsers(dest="cmd")
    p_val = sub.add_parser("validate", help="parse and show AST")
    p_val.add_argument("file")
    p_trans = sub.add_parser("translate", help="translate to LangGraph-like JSON")
    p_trans.add_argument("file")
    p_run = sub.add_parser("run", help="run program in mock mode")
    p_run.add_argument("file")
    p_run.add_argument("--allow-storage", dest="allow_storage", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "validate":
        cmd_validate(args.file)
    elif args.cmd == "translate":
        cmd_translate(args.file)
    elif args.cmd == "run":
        cmd_run(args.file, allow_storage=args.allow_storage)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(sys.argv[1:])

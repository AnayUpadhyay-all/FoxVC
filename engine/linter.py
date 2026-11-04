"""
FoxVC Static Analysis Linter (foxvc lint)
Analyzes .fox programs for unused variables, unmutated shifts,
unreachable code, and syntax violations without executing code.
"""

import os
import sys
import re
from dataclasses import dataclass
from typing import List, Dict, Set, Optional

from engine.lexer import Lexer
from engine.parser import Parser


@dataclass
class LintMessage:
    code: str
    severity: str  # "warning" | "error" | "info"
    line: int
    col: int
    message: str
    source_line: str = ""


class FoxLinter:
    """Static analyzer for FoxVC source code."""

    def __init__(self, strict: bool = False):
        self.strict = strict

    def lint_source(self, source: str, filepath: str = "<source>") -> List[LintMessage]:
        messages: List[LintMessage] = []
        lines = source.splitlines()

        def get_line(ln: int) -> str:
            return lines[ln - 1].strip() if 1 <= ln <= len(lines) else ""

        # Step 1: Lexical & Syntax Verification
        try:
            tokens = Lexer(source).tokenize()
        except Exception as e:
            msg = str(e)
            line = 1
            col = 1
            line_match = re.search(r'line\s+(\d+)', msg, re.IGNORECASE)
            col_match = re.search(r'col(?:umn)?\s+(\d+)', msg, re.IGNORECASE)
            if line_match:
                line = int(line_match.group(1))
            if col_match:
                col = int(col_match.group(1))
            messages.append(LintMessage("E001", "error", line, col, f"Syntax Error: {msg}", get_line(line)))
            return messages

        try:
            ast = Parser(tokens).parse()
        except Exception as e:
            msg = str(e)
            line = 1
            col = 1
            line_match = re.search(r'line\s+(\d+)', msg, re.IGNORECASE)
            if line_match:
                line = int(line_match.group(1))
            messages.append(LintMessage("E002", "error", line, col, f"Parser Error: {msg}", get_line(line)))
            return messages

        # Step 2: Semantic Symbol Analysis
        # Track variable definitions: name -> (kind: 'lock'|'shift', line, col, is_mutated, is_read)
        declared_vars: Dict[str, List] = {}
        mutated_vars: Set[str] = set()
        read_vars: Set[str] = set()

        for idx, token in enumerate(tokens):
            val = getattr(token, "value", str(token))
            t_type = getattr(token, "type", "")
            t_line = getattr(token, "line", 1)
            t_col = getattr(token, "col", 1)

            # Check variable declaration: lock x = ... or shift x = ...
            if val in ("lock", "shift") and idx + 1 < len(tokens):
                next_tok = tokens[idx + 1]
                var_name = getattr(next_tok, "value", str(next_tok))
                if getattr(next_tok, "type", "") == "IDENTIFIER" or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(var_name)):
                    declared_vars[var_name] = [val, t_line, t_col, False, False]

            # Check mutation: var_name = ... (where var_name is preceded by newline or not by lock/shift/act)
            if val == "=" and idx > 0:
                prev_tok = tokens[idx - 1]
                prev_name = getattr(prev_tok, "value", str(prev_tok))
                prev_type = getattr(prev_tok, "type", "")
                if prev_type == "IDENTIFIER" or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(prev_name)):
                    is_decl = False
                    if idx >= 2:
                        decl_kw = getattr(tokens[idx - 2], "value", "")
                        if decl_kw in ("lock", "shift"):
                            is_decl = True
                    if not is_decl:
                        mutated_vars.add(prev_name)
                        # Check mutating a locked variable!
                        if prev_name in declared_vars and declared_vars[prev_name][0] == "lock":
                            messages.append(
                                LintMessage(
                                    "E003", "error", t_line, t_col,
                                    f"Illegal mutation: variable '{prev_name}' was declared with immutable 'lock'.",
                                    get_line(t_line)
                                )
                            )

            # Check reading identifiers (not in declaration position)
            if t_type == "IDENTIFIER" or re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', str(val)):
                is_after_decl = (idx > 0 and getattr(tokens[idx - 1], "value", "") in ("lock", "shift", "act", "fuse", "mold"))
                is_assign_target = (idx + 1 < len(tokens) and getattr(tokens[idx + 1], "value", "") == "=")
                if not is_after_decl and not is_assign_target:
                    read_vars.add(val)

        # Check W001: shift declared but never mutated -> suggest lock
        for var_name, info in declared_vars.items():
            kind, d_line, d_col, _, _ = info
            if kind == "shift" and var_name not in mutated_vars:
                messages.append(
                    LintMessage(
                        "W001", "warning", d_line, d_col,
                        f"Variable '{var_name}' is declared with mutable 'shift' but never mutated; consider using 'lock'.",
                        get_line(d_line)
                    )
                )

            # Check W002: Variable declared but never read
            if var_name not in read_vars and not var_name.startswith("_"):
                messages.append(
                    LintMessage(
                        "W002", "warning", d_line, d_col,
                        f"Variable '{var_name}' is declared but never used.",
                        get_line(d_line)
                    )
                )

        # Step 3: Unreachable Code Detection after emit / halt / skip
        for idx, token in enumerate(tokens):
            val = getattr(token, "value", "")
            t_line = getattr(token, "line", 1)
            t_col = getattr(token, "col", 1)

            if val in ("emit", "halt", "skip"):
                # Check if there is another statement on the next line within the same block before '}'
                # Simple check: next non-comment line before '}' at same or greater indentation
                line_no = t_line
                if line_no < len(lines):
                    next_content = lines[line_no].strip()
                    if next_content and not next_content.startswith("}") and not next_content.startswith("#") and not next_content.startswith("//"):
                        # If inside block and not a closing brace
                        messages.append(
                            LintMessage(
                                "W003", "warning", line_no + 1, 1,
                                f"Unreachable code detected after '{val}' statement.",
                                get_line(line_no + 1)
                            )
                        )

        # Sort messages by line and column
        messages.sort(key=lambda m: (m.line, m.col))
        return messages

    def lint_file(self, filepath: str) -> List[LintMessage]:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        return self.lint_source(code, filepath)


def lint_cli(args: List[str]) -> int:
    """CLI handler for `foxvc lint`."""
    strict = "--strict" in args
    paths = [a for a in args if not a.startswith("-")]
    if not paths:
        paths = ["."]

    linter = FoxLinter(strict=strict)
    target_files = []

    for p in paths:
        if os.path.isfile(p):
            if p.endswith(".fox"):
                target_files.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in files:
                    if f.endswith(".fox"):
                        target_files.append(os.path.join(root, f))

    if not target_files:
        print("foxvc lint: No .fox files found to lint.")
        return 0

    total_warnings = 0
    total_errors = 0

    for tf in target_files:
        messages = linter.lint_file(tf)
        if not messages:
            continue

        rel_path = os.path.relpath(tf)
        print(f"\n📄 {rel_path}:")
        for m in messages:
            if m.severity == "error":
                total_errors += 1
                badge = "\033[91m[ERROR]\033[0m"
            else:
                total_warnings += 1
                badge = "\033[93m[WARN]\033[0m"

            print(f"  {badge} [{m.code}] Line {m.line}:{m.col} — {m.message}")
            if m.source_line:
                print(f"      \033[90m{m.line:3d} | {m.source_line}\033[0m")

    print("\n--------------------------------------------------")
    if total_errors == 0 and total_warnings == 0:
        print("✓ All FoxVC files passed static linting with 0 issues.")
        return 0
    else:
        print(f"Lint Summary: {total_errors} error(s), {total_warnings} warning(s)")
        if total_errors > 0 or (strict and total_warnings > 0):
            return 1
        return 0

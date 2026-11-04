"""
FoxVC Canonical Code Formatter (foxvc fmt)
Enforces consistent, idiomatic 4-space indentation, binary operator spacing,
and clean block structure for .fox programs while strictly protecting string literals.
"""

import os
import sys
import re
from typing import List, Tuple, Optional


class FoxFormatter:
    """Canonical syntax and indentation formatter for FoxVC source code."""

    def __init__(self, indent_size: int = 4):
        self.indent_size = indent_size
        self.indent_str = " " * indent_size

    def format_source(self, source: str) -> str:
        """Formats the given FoxVC source string into canonical style."""
        lines = source.splitlines()
        formatted_lines = []
        prev_was_blank = False

        for raw_line in lines:
            # Preserve leading indentation amount
            stripped = raw_line.strip()

            if not stripped:
                if not prev_was_blank and formatted_lines:
                    formatted_lines.append("")
                    prev_was_blank = True
                continue

            prev_was_blank = False

            # Measure existing leading spaces
            leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
            # Normalize tab to 4 spaces
            if "\t" in raw_line[:leading_spaces]:
                raw_leading = raw_line[:leading_spaces].replace("\t", self.indent_str)
                leading_spaces = len(raw_leading)

            # Align leading spaces to multiple of indent_size
            if leading_spaces > 0:
                norm_level = max(1, (leading_spaces + self.indent_size // 2) // self.indent_size)
            else:
                norm_level = 0
            norm_indent = self.indent_str * norm_level

            # Format the content while strictly preserving strings and comments
            formatted_content = self._format_line_content(stripped)

            formatted_lines.append(norm_indent + formatted_content)

        result = "\n".join(formatted_lines).rstrip() + "\n"
        return result

    def _format_line_content(self, line: str) -> str:
        """Normalizes spacing around keywords, operators, and delimiters outside strings."""
        if line.startswith("#") or line.startswith("//"):
            return line

        # Split line into tokens of (is_str, is_comment, text)
        segments = []
        n = len(line)
        i = 0
        in_str = False
        quote_char = None
        cur = []

        while i < n:
            ch = line[i]

            if in_str:
                cur.append(ch)
                if ch == "\\" and i + 1 < n:
                    i += 1
                    cur.append(line[i])
                elif ch == quote_char:
                    in_str = False
                    quote_char = None
                    segments.append((True, False, "".join(cur)))
                    cur = []
                i += 1
                continue

            # Check comment start
            if ch in ("#",) or (ch == "/" and i + 1 < n and line[i + 1] == "/"):
                if cur:
                    segments.append((False, False, "".join(cur)))
                    cur = []
                segments.append((False, True, line[i:]))
                break

            # Check string start
            if ch in ('"', "'"):
                if cur:
                    segments.append((False, False, "".join(cur)))
                    cur = []
                in_str = True
                quote_char = ch
                cur.append(ch)
                i += 1
                continue

            cur.append(ch)
            i += 1

        if cur:
            segments.append((in_str, False, "".join(cur)))

        # Format only the code segments
        result_parts = []
        for is_str, is_comment, text in segments:
            if is_str or is_comment:
                result_parts.append(text)
            else:
                formatted_code = self._normalize_code_operators(text)
                result_parts.append(formatted_code)

        combined = "".join(result_parts).rstrip()
        return combined

    def _normalize_code_operators(self, code: str) -> str:
        # Normalize multiple spaces
        s = re.sub(r'[ \t]+', ' ', code)

        # Space around comparison operators
        for op in ["==", "!=", "<=", ">="]:
            s = re.sub(rf'\s*{re.escape(op)}\s*', f' {op} ', s)

        # Space around assignment operator = (not preceded by !, <, >, = and not followed by =)
        s = re.sub(r'(?<![=!<>\+\-\*\/])\s*=\s*(?![=])', ' = ', s)

        # Space around binary arithmetic operators
        s = re.sub(r'\s*\+\s*', ' + ', s)
        s = re.sub(r'\s*-\s*', ' - ', s)
        s = re.sub(r'\s*\*\s*', ' * ', s)
        s = re.sub(r'\s*\/\s*', ' / ', s)

        # Space after comma
        s = re.sub(r'\s*,\s*', ', ', s)

        # Clean up any accidental double spaces created
        s = re.sub(r'  +', ' ', s)
        return s

    def format_file(self, filepath: str, write: bool = False) -> Tuple[bool, str]:
        with open(filepath, "r", encoding="utf-8") as f:
            original = f.read()

        formatted = self.format_source(original)
        has_changed = (original != formatted)

        if write and has_changed:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(formatted)

        return has_changed, formatted


def format_cli(args: List[str]) -> int:
    """CLI handler for `foxvc fmt`."""
    write_in_place = "-w" in args or "--write" in args
    check_only = "-c" in args or "--check" in args

    paths = [a for a in args if not a.startswith("-")]
    if not paths:
        paths = ["."]

    formatter = FoxFormatter()
    target_files = []

    for p in paths:
        if os.path.isfile(p):
            if p.endswith(".fox"):
                target_files.append(p)
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                if "venv" in root or ".git" in root or "__pycache__" in root:
                    continue
                for f in files:
                    if f.endswith(".fox"):
                        target_files.append(os.path.join(root, f))

    if not target_files:
        print("foxvc fmt: No .fox files found to format.")
        return 0

    unformatted_count = 0
    for tf in target_files:
        changed, _ = formatter.format_file(tf, write=write_in_place)
        rel_path = os.path.relpath(tf)
        if changed:
            unformatted_count += 1
            if write_in_place:
                print(f"✓ Formatted {rel_path}")
            elif check_only:
                print(f"✗ Needs formatting: {rel_path}")
            else:
                print(f"• Would format {rel_path} (use -w to write)")

    if check_only and unformatted_count > 0:
        print(f"\nfoxvc fmt: {unformatted_count} file(s) need formatting.")
        return 1

    if write_in_place:
        print(f"\nfoxvc fmt: Cleaned {unformatted_count} file(s). All files up to date.")
    elif not check_only:
        print(f"\nfoxvc fmt: Checked {len(target_files)} file(s). Run 'foxvc fmt -w' to apply changes.")

    return 0

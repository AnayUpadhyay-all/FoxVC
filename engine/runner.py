"""
FoxVC Execution Runner (v0.5.4)
Provides project execution, single file running, and diagnostic validation.
"""

import sys
import os
import time
from typing import Optional, Dict, Any

from engine.lexer import Lexer, LexerError
from engine.parser import Parser, ParserError
from engine.interpreter import Interpreter, FoxPack, RuntimeError as FoxRuntimeError


def run_foxvc_code(code: str, filename: str = "main.fox", interp: Optional[Interpreter] = None) -> Dict[str, Any]:
    """Execute raw FoxVC code string directly."""
    interp = interp or Interpreter()
    try:
        tokens = Lexer(code, filename=filename).tokenize()
        ast = Parser(tokens, filename=filename).parse()
        interp.execute(ast)
        return {
            "success": True,
            "error": None,
            "variables": interp.variables,
            "output": interp.output_buffer
        }
    except (LexerError, ParserError, FoxRuntimeError) as err:
        return {
            "success": False,
            "error": str(err),
            "variables": interp.variables,
            "output": interp.output_buffer
        }
    except Exception as err:
        return {
            "success": False,
            "error": f"Internal Engine Fault: {err}",
            "variables": interp.variables,
            "output": interp.output_buffer
        }


def run_foxvc_project(target_path: str) -> int:
    """Run a .fox file or entrypoint main.fox from a directory."""
    if os.path.isdir(target_path):
        entry_file = os.path.join(target_path, "main.fox")
    else:
        entry_file = target_path

    if not os.path.exists(entry_file):
        print(f"❌ Error: FoxVC target not found: {entry_file}", file=sys.stderr)
        return 1

    try:
        with open(entry_file, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception as e:
        print(f"❌ Failed to read source file: {e}", file=sys.stderr)
        return 1

    interp = Interpreter()
    res = run_foxvc_code(code, filename=os.path.basename(entry_file), interp=interp)

    if not res["success"]:
        print(f"\n{res['error']}", file=sys.stderr)
        return 1
    return 0


def run_foxvc_diagnostic(target_path: str = ".") -> int:
    """Runs a health and syntax check over FoxVC files without side effects."""
    print("🔍 FoxVC v0.5.4 Diagnostic Sweep...")
    files_checked = 0
    errors_found = 0

    scan_dir = target_path if os.path.isdir(target_path) else os.path.dirname(target_path) or "."
    for root, _, files in os.walk(scan_dir):
        for file in files:
            if file.endswith(".fox"):
                files_checked += 1
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        code = f.read()
                    tokens = Lexer(code, filename=file).tokenize()
                    Parser(tokens, filename=file).parse()
                    print(f"  ✓ {file} - Valid AST")
                except Exception as e:
                    errors_found += 1
                    print(f"  ✗ {file} - {e}")

    print(f"\nDiagnostic finished: {files_checked} files inspected, {errors_found} errors.")
    return 1 if errors_found > 0 else 0

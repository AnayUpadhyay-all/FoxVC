
def format_fox_diagnostic(err: Exception, source: str, line_no: int = None, filename: str = "<script>") -> str:
    msg = str(err)
    if not line_no or not source:
        return f"\n\033[1;31m[FoxVC Runtime Error]\033[0m: {msg}\n"
    
    lines = source.splitlines()
    snippet = ""
    if 1 <= line_no <= len(lines):
        line_content = lines[line_no - 1]
        snippet = f"\n  --> {filename}:{line_no}\n   |\n{line_no:2d} | {line_content}\n   | \033[1;31m^^^^\033[0m"
    
    return f"\n\033[1;31m[FoxVC Runtime Error]\033[0m: {msg}{snippet}\n"


def format_fox_error(err: Exception, source: str = "") -> str:
    msg = str(err)
    return f"\n\033[1;31m[FoxVC Runtime Error]\033[0m: {msg}\n"

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
from engine.interpreter import Interpreter, FoxPack, RuntimeError as FoxRuntimeError, EmitSignal


def run_foxvc_code(code: str, filename: str = "<memory>", interp: Interpreter = None) -> dict:
    if interp is None:
        interp = Interpreter()

    from engine.lexer import Lexer
    from engine.parser import Parser
    from engine.bytecode import BytecodeCompiler
    from engine.c_vm import FoxCVM

    try:
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()

        # Fast Bytecode + C Path
        try:
            compiler = BytecodeCompiler()
            pkg = compiler.compile(ast)
            instructions = pkg[0] if isinstance(pkg, (tuple, list)) else pkg

            cvm = FoxCVM()
            res = cvm.run(instructions)
            return {
                "success": True,
                "error": None,
                "emitted": res,
                "variables": interp.variables,
                "output": interp.output_buffer
            }
        except Exception as vm_err:
            if os.environ.get("FOX_DEBUG") or os.environ.get("DEBUG"):
                sys.stderr.write(f"\033[33m[FoxCVM Fallback Warning]: {vm_err}\033[0m\n")
            # Fallback to Tree-Walker if C runtime hits an uncompiled dynamic node
            interp.execute(ast)
            return {
                "success": True,
                "error": None,
                "emitted": getattr(interp, "last_emitted", None),
                "variables": interp.variables,
                "output": interp.output_buffer
            }
    except EmitSignal as sig:
        return {
            "success": True,
            "error": None,
            "emitted": sig.value,
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
    """Run a .fox or .foxc file, or entrypoint main.fox from a directory."""
    if os.path.isdir(target_path):
        entry_file = os.path.join(target_path, "main.fox")
    else:
        entry_file = target_path

    if not os.path.exists(entry_file):
        print(f"❌ Error: FoxVC target not found: {entry_file}", file=sys.stderr)
        return 1

    if entry_file.endswith(".foxc"):
        try:
            from engine.c_vm import FoxCVM
            cvm = FoxCVM()
            cvm.run_foxc(entry_file)
            return 0
        except Exception as e:
            print(f"❌ Error running AOT bytecode '{entry_file}': {e}", file=sys.stderr)
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


def run_fast(source_code: str, debug: bool = False):
    """
    High-Performance Execution Pipeline:
    Tries Native C Extension (-O3) first -> falls back to Python Bytecode VM.
    """
    import os, subprocess
    from engine.lexer import Lexer
    from engine.parser import Parser
    from engine.bytecode import BytecodeCompiler, FoxVM

    ast = Parser(Lexer(source_code).tokenize(), source=source_code).parse()
    compiler = BytecodeCompiler()
    code = compiler.compile(ast)

    if debug:
        print("--- COMPILED INSTRUCTIONS ---")
        for i, inst in enumerate(code):
            print(f"{i:02d}: {inst[0].name} {inst[1:]}")

    # Try Native C Extension
    try:
        from engine.c_vm import FoxCVM
        so_path = os.path.join(os.path.dirname(__file__), 'foxvm.so')
        c_path = os.path.join(os.path.dirname(__file__), 'foxvm.c')
        if not os.path.exists(so_path) and os.path.exists(c_path):
            subprocess.run(['gcc', '-O3', '-shared', '-fPIC', c_path, '-o', so_path], check=True)
        return FoxCVM().run(code)
    except Exception as e:
        if debug:
            print(f"[VM Warning]: Native C VM fallback triggered: {e}")
        return FoxVM().run(code)


def run_foxvc(source: str, engine_mode: str = 'interp', debug: bool = False):
    """
    Multi-Tier Execution Dispatcher for FoxVC:
    - 'interp' : Tree-walking interpreter (v0.5.4 default)
    - 'vm'     : Pure Python Register Bytecode VM (v0.6)
    - 'fast'   : Native C Extension VM with auto-fallback (-O3)
    """
    from engine.lexer import Lexer
    from engine.parser import Parser

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens, source=source).parse()

    if engine_mode == 'interp':
        from engine.interpreter import Interpreter, EmitSignal
        interp = Interpreter()
        try:
            interp.execute(ast)
            return None
        except EmitSignal as sig:
            return sig.value

    elif engine_mode in ('vm', 'fast'):
        from engine.bytecode import BytecodeCompiler, FoxVM
        compiler = BytecodeCompiler()
        code_pkg = compiler.compile(ast)

        if debug:
            code, funcs = code_pkg
            print('--- BYTECODE ---')
            for i, inst in enumerate(code):
                print(f'{i:02d}: {inst[0].name} {inst[1:]}')

        if engine_mode == "fast":
            from engine.c_vm import FoxCVM
            instructions = code_pkg[0] if isinstance(code_pkg, tuple) else code_pkg
            functions = code_pkg[1] if isinstance(code_pkg, tuple) else {}
            if FoxCVM.can_accelerate(instructions, functions):
                try:
                    return FoxCVM().run(instructions)
                except Exception as e:
                    if debug:
                        print(f"[FoxCVM Fallback]: {e}")
            elif debug:
                print("[Hybrid Router]: Script uses dynamic features; executing on FoxVM.")

        try:
            vm = FoxVM()
            return vm.run(code_pkg)
        except Exception as e:
            sys.stderr.write(format_fox_diagnostic(e, source, getattr(vm, "line_map", {}).get(getattr(vm, "ip", 0), 1)))
            return None

"""
FoxVC Execution Runner (v0.5.4)
Provides multi-tier deterministic project execution, single file running,
differential validation, and diagnostic inspection.
"""

import sys
import os
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from engine.lexer import Lexer, LexerError
from engine.parser import Parser, ParserError
from engine.interpreter import Interpreter, FoxPack, RuntimeError as FoxRuntimeError, EmitSignal


def format_fox_diagnostic(err: Exception, source: str, line_no: int = None, filename: str = "<script>") -> str:
    msg = str(err)
    from engine.friendly_errors import explain_error_in_everyday_language
    hint = explain_error_in_everyday_language(msg, source)
    hint_str = f"\n\033[36m{hint}\033[0m\n" if hint else ""

    if not line_no or not source:
        return f"\n\033[1;31m[FoxVC Runtime Error]\033[0m: {msg}\n{hint_str}"

    lines = source.splitlines()
    snippet = ""
    if 1 <= line_no <= len(lines):
        line_content = lines[line_no - 1]
        snippet = f"\n  --> {filename}:{line_no}\n   |\n{line_no:2d} | {line_content}\n   | \033[1;31m^^^^\033[0m"

    return f"\n\033[1;31m[FoxVC Runtime Error]\033[0m: {msg}{snippet}\n{hint_str}"


def format_fox_error(err: Exception, source: str = "") -> str:
    msg = str(err)
    return f"\n\033[1;31m[FoxVC Runtime Error]\033[0m: {msg}\n"


@dataclass
class ExecutionResult:
    """Authoritative execution result container across all FoxVC engines."""
    success: bool
    output: str = ""
    error: Optional[str] = None
    value: Any = None
    variables: Dict[str, Any] = field(default_factory=dict)
    engine: str = "interp"

    def __getitem__(self, key: str) -> Any:
        if key == "success":
            return self.success
        if key == "output":
            return self.output
        if key == "error":
            return self.error
        if key in ("emitted", "value"):
            return self.value
        if key == "variables":
            return self.variables
        if key == "engine":
            return self.engine
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


def run_foxvc(
    source: Optional[str],
    engine_mode: str = 'interp',
    debug: bool = False,
    as_result: bool = True,
    sandboxed: bool = False,
    allowed_dir: Optional[str] = None,
    allow_fallback: bool = False,
    timeout: Optional[float] = None,
    filename: str = "main.fox",
    input_source: Any = None,
    file_path: Optional[str] = None
) -> Any:
    """
    Multi-Tier Execution Dispatcher for FoxVC:
    - 'interp' : Tree-walking interpreter (authoritative semantics)
    - 'vm'     : Pure Python Register Bytecode VM
    - 'fast'   : Native C Extension VM (strictly validated, explicit opt-in fallback)
    """
    fname = file_path or filename or "main.fox"
    src = "" if source is None else str(source)

    if not src.strip():
        res = ExecutionResult(success=True, output="", value=None, engine=engine_mode)
        return res if as_result else res.value

    if engine_mode == 'interp':
        interp = Interpreter(sandboxed=sandboxed, allowed_dir=allowed_dir, input_source=input_source)
        try:
            tokens = Lexer(src, filename=fname).tokenize()
            ast = Parser(tokens, filename=fname, source=src).parse()
            interp.execute(ast)
            res = ExecutionResult(
                success=True,
                output="\n".join(interp.output_buffer),
                value=getattr(interp, "last_emitted", None),
                variables=dict(interp.variables.items()),
                engine="interp"
            )
        except EmitSignal as sig:
            res = ExecutionResult(
                success=True,
                output="\n".join(interp.output_buffer),
                value=sig.value,
                variables=dict(interp.variables.items()),
                engine="interp"
            )
        except (LexerError, ParserError, FoxRuntimeError) as err:
            from engine.friendly_errors import explain_error_in_everyday_language
            hint = explain_error_in_everyday_language(str(err), src)
            err_text = f"{err}\n\n\033[36m{hint}\033[0m" if hint else str(err)
            res = ExecutionResult(
                success=False,
                output="\n".join(interp.output_buffer),
                error=err_text,
                variables=dict(interp.variables.items()),
                engine="interp"
            )
        except Exception as err:
            res = ExecutionResult(
                success=False,
                output="\n".join(interp.output_buffer),
                error=f"Runtime Fault: {err}",
                variables=dict(interp.variables.items()),
                engine="interp"
            )

    elif engine_mode == 'vm':
        from engine.bytecode import BytecodeCompiler, FoxVM
        vm = FoxVM()
        try:
            tokens = Lexer(src, filename=fname).tokenize()
            ast = Parser(tokens, filename=fname, source=src).parse()
            compiler = BytecodeCompiler()
            code_pkg = compiler.compile(ast)

            if debug:
                code = code_pkg[0] if isinstance(code_pkg, tuple) else code_pkg
                print('--- BYTECODE ---')
                for i, inst in enumerate(code):
                    print(f'{i:02d}: {inst[0].name} {inst[1:]}')

            val = vm.run(code_pkg)
            res = ExecutionResult(
                success=True,
                output="\n".join(vm.output_buffer),
                value=val,
                variables=dict(vm.globals),
                engine="vm"
            )
        except Exception as err:
            line_no = getattr(vm, "line_map", {}).get(getattr(vm, "ip", 0), 1)
            err_msg = format_fox_diagnostic(err, src, line_no, fname)
            if debug:
                sys.stderr.write(err_msg)
            res = ExecutionResult(
                success=False,
                output="\n".join(getattr(vm, "output_buffer", [])),
                error=err_msg.strip(),
                engine="vm"
            )

    elif engine_mode == 'fast':
        from engine.bytecode import BytecodeCompiler, FoxVM
        from engine.c_vm import FoxCVM

        try:
            tokens = Lexer(src, filename=fname).tokenize()
            ast = Parser(tokens, filename=fname, source=src).parse()
            compiler = BytecodeCompiler()
            code_pkg = compiler.compile(ast)
            instructions = code_pkg[0] if isinstance(code_pkg, tuple) else code_pkg
            functions = code_pkg[1] if isinstance(code_pkg, tuple) else {}

            can_acc = FoxCVM.can_accelerate(instructions, functions)
            if not can_acc:
                if not allow_fallback:
                    raise NotImplementedError(
                        "Native C VM (FoxCVM) cannot accelerate this script (unsupported dynamic opcodes or external calls). "
                        "Execute with engine_mode='vm' or pass allow_fallback=True."
                    )
                if debug:
                    print("[Hybrid Router]: Script uses dynamic features; explicitly falling back to FoxVM.")
                vm = FoxVM()
                val = vm.run(code_pkg)
                res = ExecutionResult(
                    success=True,
                    output="\n".join(vm.output_buffer),
                    value=val,
                    variables=dict(vm.globals),
                    engine="vm"
                )
            else:
                cvm = FoxCVM()
                val = cvm.run(instructions)
                res = ExecutionResult(
                    success=True,
                    output="",
                    value=val,
                    engine="fast"
                )
        except Exception as err:
            if allow_fallback and 'code_pkg' in locals():
                if debug:
                    print(f"[FoxCVM Fallback]: {err}; explicitly executing on FoxVM.")
                try:
                    vm = FoxVM()
                    val = vm.run(code_pkg)
                    res = ExecutionResult(
                        success=True,
                        output="\n".join(vm.output_buffer),
                        value=val,
                        variables=dict(vm.globals),
                        engine="vm"
                    )
                except Exception as vm_err:
                    res = ExecutionResult(
                        success=False,
                        output="",
                        error=f"[FoxVM Error after Native Fallback]: {vm_err}",
                        engine="vm"
                    )
            else:
                res = ExecutionResult(
                    success=False,
                    output="",
                    error=f"[FoxCVM Error]: {err}",
                    engine="fast"
                )
    else:
        raise ValueError(f"Unknown engine mode '{engine_mode}'. Supported modes: 'interp', 'vm', 'fast'.")

    return res if as_result else res.value


def run_foxvc_code(
    code: str,
    filename: str = "<memory>",
    interp: Optional[Interpreter] = None,
    sandboxed: bool = False,
    allowed_dir: Optional[str] = None
) -> ExecutionResult:
    """Execute raw FoxVC code string returning an authoritative ExecutionResult."""
    return run_foxvc(
        code,
        engine_mode='interp',
        as_result=True,
        sandboxed=sandboxed,
        allowed_dir=allowed_dir,
        filename=filename
    )


def run_fast(source_code: str, debug: bool = False, allow_fallback: bool = False) -> Any:
    """
    High-Performance Execution Pipeline:
    Executes via Native C VM if supported; strictly reports unsupported features unless allow_fallback is enabled.
    """
    return run_foxvc(
        source_code,
        engine_mode='fast',
        debug=debug,
        as_result=False,
        allow_fallback=allow_fallback
    )


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

    res = run_foxvc(code, filename=os.path.basename(entry_file), as_result=True)
    if not res.success:
        print(f"\n{res.error}", file=sys.stderr)
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

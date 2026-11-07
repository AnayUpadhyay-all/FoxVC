"""
FoxVC Standalone Binary Compiler (foxvc build)
Transforms .fox source code into a standalone, portable native executable
with zero host runtime dependencies.
"""
import os
import sys
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict, Any

from engine.lexer import Lexer
from engine.parser import Parser
from engine.bytecode import BytecodeCompiler
from engine.c_vm import FoxCVM
from engine.version import FOXVC_LANGUAGE_VERSION, FOXVC_ENGINE_VERSION


class BuildError(Exception):
    """Raised when compilation to native binary fails."""
    pass


@dataclass
class BuildResult:
    success: bool
    source_path: str
    output_path: str
    binary_size_bytes: int
    bytecode_len: int
    num_consts_len: int
    str_consts_len: int
    compiler_used: Optional[str] = None
    target: str = "c_binary"
    error: Optional[str] = None


# Supported cross-compilation targets mapped to LLVM triples and default binary extensions
SUPPORTED_TARGETS: Dict[str, Tuple[str, str]] = {
    # Linux
    "linux": ("x86_64-unknown-linux-gnu", ""),
    "linux-x64": ("x86_64-unknown-linux-gnu", ""),
    "linux-arm64": ("aarch64-unknown-linux-gnu", ""),
    "linux-arm": ("armv7-unknown-linux-gnueabihf", ""),
    # Windows (PE/COFF 64-bit)
    "windows": ("x86_64-w64-mingw32", ".exe"),
    "win": ("x86_64-w64-mingw32", ".exe"),
    "win64": ("x86_64-w64-mingw32", ".exe"),
    "win-arm64": ("aarch64-pc-windows-msvc", ".exe"),
    # macOS (Darwin Mach-O)
    "macos": ("aarch64-apple-darwin", ""),
    "darwin": ("aarch64-apple-darwin", ""),
    "mac-arm64": ("aarch64-apple-darwin", ""),
    "mac-x64": ("x86_64-apple-darwin", ""),
    # WebAssembly (WASI)
    "wasm": ("wasm32-unknown-wasi", ".wasm"),
    "wasm32": ("wasm32-unknown-wasi", ".wasm"),
    "webassembly": ("wasm32-unknown-wasi", ".wasm"),
    # Android
    "android": ("aarch64-linux-android", ""),
    "android-arm64": ("aarch64-linux-android", ""),
}


class StandaloneCompiler:
    """Compiles FoxVC source files into standalone native executable binaries using C/LLVM."""

    def __init__(self):
        self.foxvm_c_path = os.path.join(os.path.dirname(__file__), "foxvm.c")
        if not os.path.exists(self.foxvm_c_path):
            raise FileNotFoundError(f"FoxVM C runtime engine template not found at {self.foxvm_c_path}")

    @staticmethod
    def resolve_target(target_name: Optional[str]) -> Tuple[Optional[str], str]:
        """
        Resolves a target alias into (llvm_target_triple, default_extension).
        Returns (None, '') for native host compilation.
        """
        if not target_name or target_name.lower().strip() in ("host", "native", "local"):
            return None, ".exe" if sys.platform == "win32" else ""

        normalized = target_name.lower().strip()
        if normalized in SUPPORTED_TARGETS:
            return SUPPORTED_TARGETS[normalized]

        ext = ".exe" if ("windows" in normalized or "mingw" in normalized) else (".wasm" if "wasm" in normalized else "")
        return normalized, ext

    @staticmethod
    def find_c_compiler(target_triple: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Locates an available C/LLVM compiler on the host system.
        Prioritizes Clang (LLVM) for multi-target support and specialized cross-compilers.
        Returns tuple of (compiler_path, compiler_type: 'clang' | 'gcc' | 'cl' | 'mingw').
        """
        # If targeting Windows, check for mingw-w64 toolchains first
        if target_triple and ("mingw" in target_triple or "windows" in target_triple):
            for mingw_name in ["x86_64-w64-mingw32-gcc", "x86_64-w64-mingw32-clang"]:
                p = shutil.which(mingw_name)
                if p:
                    return p, "mingw"

        # Prioritize Clang (LLVM) because it has universal cross-target backends built in
        for name, ctype in [("clang", "clang"), ("gcc", "gcc"), ("cc", "gcc"), ("cl", "cl")]:
            path = shutil.which(name)
            if path:
                return path, ctype
        return None

    @staticmethod
    def _escape_c_string(s: str) -> str:
        """Escapes a Python string for literal inclusion in a C source string."""
        escaped = []
        for char in s:
            if char == '\\':
                escaped.append('\\\\')
            elif char == '"':
                escaped.append('\\"')
            elif char == '\n':
                escaped.append('\\n')
            elif char == '\r':
                escaped.append('\\r')
            elif char == '\t':
                escaped.append('\\t')
            else:
                escaped.append(char)
        return "".join(escaped)

    def generate_c_source(
        self,
        flat_inst: List[int],
        num_consts: List[float],
        str_consts: List[str],
        raylib: bool = False,
        source_name: str = "program.fox"
    ) -> str:
        """Generates self-contained C source code embedding bytecode and the C VM."""
        with open(self.foxvm_c_path, "r", encoding="utf-8") as f:
            c_runner_code = f.read()

        # Format arrays for C embedding
        if flat_inst:
            bytecode_chunks = [", ".join(str(x) for x in flat_inst[i:i+20]) for i in range(0, len(flat_inst), 20)]
            bytecode_str = ",\n    ".join(bytecode_chunks)
        else:
            bytecode_str = "17 /* HALT */"

        if num_consts:
            nums_chunks = [", ".join(f"{float(x):.17g}" for x in num_consts[i:i+10]) for i in range(0, len(num_consts), 10)]
            nums_str = ",\n    ".join(nums_chunks)
        else:
            nums_str = "0.0"

        if str_consts:
            strs_formatted = [f'"{self._escape_c_string(s)}"' for s in str_consts]
            strs_chunks = [", ".join(strs_formatted[i:i+5]) for i in range(0, len(strs_formatted), 5)]
            strs_str = ",\n    ".join(strs_chunks)
        else:
            strs_str = '""'

        raylib_def = "#define FOX_ENABLE_RAYLIB 1\n" if raylib else "/* FOX_ENABLE_RAYLIB disabled for zero-dependency build */\n"

        header = f"""/*
 * ============================================================================
 * FoxVC Standalone Executable Binary
 * Source: {source_name}
 * Language Spec: v{FOXVC_LANGUAGE_VERSION} | Engine: v{FOXVC_ENGINE_VERSION}
 * Generated by FoxVC Standalone Compiler (foxvc build)
 * Zero Host Dependencies - Pure Standalone Native Binary
 * ============================================================================
 */

{raylib_def}
"""

        main_entry = f"""
/* --- EMBEDDED FOXVC BYTECODE PAYLOAD --- */
static int FOX_EMBEDDED_BYTECODE[] = {{
    {bytecode_str}
}};
static const int FOX_EMBEDDED_BYTECODE_LEN = sizeof(FOX_EMBEDDED_BYTECODE) / sizeof(FOX_EMBEDDED_BYTECODE[0]);

static double FOX_EMBEDDED_NUM_CONSTS[] = {{
    {nums_str}
}};
static const int FOX_EMBEDDED_NUM_CONSTS_LEN = sizeof(FOX_EMBEDDED_NUM_CONSTS) / sizeof(FOX_EMBEDDED_NUM_CONSTS[0]);

static const char* FOX_EMBEDDED_STR_CONSTS[] = {{
    {strs_str}
}};
static const int FOX_EMBEDDED_STR_CONSTS_LEN = sizeof(FOX_EMBEDDED_STR_CONSTS) / sizeof(FOX_EMBEDDED_STR_CONSTS[0]);

int main(int argc, char** argv) {{
    run_bytecode(
        FOX_EMBEDDED_BYTECODE,
        FOX_EMBEDDED_BYTECODE_LEN,
        FOX_EMBEDDED_NUM_CONSTS,
        FOX_EMBEDDED_NUM_CONSTS_LEN,
        FOX_EMBEDDED_STR_CONSTS,
        FOX_EMBEDDED_STR_CONSTS_LEN
    );
    return 0;
}}
"""
        return header + c_runner_code + main_entry

    def build(
        self,
        source_path: str,
        output_path: Optional[str] = None,
        emit_c: bool = False,
        emit_llvm: bool = False,
        target: Optional[str] = None,
        opt_level: str = "2",
        raylib: bool = False,
        verbose: bool = False
    ) -> BuildResult:
        """
        Builds a .fox source file into a native binary executable, LLVM IR, or C source.
        Supports multi-target cross-compilation via LLVM (Windows, macOS, Linux, WebAssembly, Android).
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source file not found: {source_path}")

        with open(source_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        # Step 1: Lex & Parse
        tokens = Lexer(source_code, filename=source_path).tokenize()
        ast = Parser(tokens, filename=source_path, source=source_code).parse()

        # Step 2: Compile to FoxVC Bytecode
        compiler = BytecodeCompiler()
        code_pkg = compiler.compile(ast)

        # Step 3: Flatten to C-compatible bytecode
        cvm = FoxCVM()
        try:
            flat_inst, num_consts, str_consts = cvm.compile_payload(code_pkg)
        except Exception as e:
            raise BuildError(f"C VM compilation error: {str(e)}")

        # Determine target architecture and file extensions
        target_triple, default_ext = self.resolve_target(target)
        base_name = os.path.splitext(os.path.basename(source_path))[0]
        dir_name = os.path.dirname(os.path.abspath(source_path))

        # Mode A: Emit C Source Code
        if emit_c:
            target_out = output_path or os.path.join(dir_name, f"{base_name}.c")
            c_code = self.generate_c_source(flat_inst, num_consts, str_consts, raylib=raylib, source_name=source_path)
            with open(target_out, "w", encoding="utf-8") as f:
                f.write(c_code)
            file_size = os.path.getsize(target_out)
            return BuildResult(
                success=True,
                source_path=source_path,
                output_path=target_out,
                binary_size_bytes=file_size,
                bytecode_len=len(flat_inst),
                num_consts_len=len(num_consts),
                str_consts_len=len(str_consts),
                compiler_used=None,
                target="c_source"
            )

        # Step 4: Compiler Discovery (Prioritizes Clang/LLVM for cross-targeting)
        compiler_info = self.find_c_compiler(target_triple=target_triple)
        if not compiler_info:
            raise BuildError(
                "No C/LLVM compiler found on this system (clang, gcc, or cl.exe).\n"
                "Please install clang ('sudo apt install clang' or 'brew install llvm'), or use '--emit-c'."
            )

        compiler_path, compiler_type = compiler_info

        # Generate C source into temporary file
        c_code = self.generate_c_source(flat_inst, num_consts, str_consts, raylib=raylib, source_name=source_path)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False, encoding="utf-8") as temp_c:
            temp_c_path = temp_c.name
            temp_c.write(c_code)

        try:
            opt_flag = f"-O{opt_level}" if opt_level in ("0", "1", "2", "3", "s") else "-O2"
            include_dir = os.path.join(os.path.dirname(__file__), "include")

            # Mode B: Emit LLVM IR (.ll)
            if emit_llvm:
                target_out = output_path or os.path.join(dir_name, f"{base_name}.ll")
                if compiler_type != "clang":
                    # Check if clang is available specifically for LLVM IR emission
                    clang_path = shutil.which("clang")
                    if clang_path:
                        compiler_path = clang_path
                    else:
                        raise BuildError("--emit-llvm requires Clang/LLVM installed ('sudo apt install clang')")

                cmd = [compiler_path, "-S", "-emit-llvm", opt_flag, temp_c_path, "-o", target_out]
                if target_triple:
                    cmd.extend(["--target=" + target_triple])
                if os.path.exists(include_dir):
                    cmd.extend(["-I", include_dir])

                if verbose:
                    print(f"[FoxVC Builder] Emitting LLVM IR via: {' '.join(cmd)}")

                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if res.returncode != 0:
                    raise BuildError(f"LLVM IR emission failed:\n{res.stderr.strip()}")

                file_size = os.path.getsize(target_out)
                return BuildResult(
                    success=True,
                    source_path=source_path,
                    output_path=target_out,
                    binary_size_bytes=file_size,
                    bytecode_len=len(flat_inst),
                    num_consts_len=len(num_consts),
                    str_consts_len=len(str_consts),
                    compiler_used=f"{os.path.basename(compiler_path)} (LLVM IR)",
                    target=target_triple or "llvm_ir"
                )

            # Mode C: Native Binary Compilation (Host or Cross-OS)
            default_binary_name = (base_name + default_ext) if default_ext else (
                f"{base_name}.exe" if (target_triple and "windows" in target_triple) else base_name
            )
            target_binary = output_path or os.path.join(dir_name, default_binary_name)

            if compiler_type in ("gcc", "clang", "mingw"):
                cmd = [compiler_path, opt_flag]
                if target_triple and compiler_type == "clang":
                    cmd.extend(["--target=" + target_triple])
                cmd.extend(["-s", temp_c_path, "-o", target_binary, "-lm"])
                if os.path.exists(include_dir):
                    cmd.extend(["-I", include_dir])
                if raylib:
                    cmd.append("-lraylib")
            elif compiler_type == "cl":
                cmd = [compiler_path, f"/O{opt_level}", temp_c_path, f"/Fe:{target_binary}"]
                if os.path.exists(include_dir):
                    cmd.extend([f"/I{include_dir}"])
            else:
                cmd = [compiler_path, temp_c_path, "-o", target_binary, "-lm"]

            if verbose:
                print(f"[FoxVC Builder] Invoking compiler: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            if result.returncode != 0:
                err_msg = result.stderr.strip()
                if "bits/libc-header-start.h" in err_msg or "bits/" in err_msg or "sysroot" in err_msg:
                    err_msg += (
                        f"\n\n💡 Cross-Compilation Tip:"
                        f"\n   Cross-compiling to '{target_triple}' requires the target OS sysroot/headers."
                        f"\n   - For Windows: install mingw-w64 ('sudo apt install mingw-w64')"
                        f"\n   - For ARM64: install gcc-aarch64-linux-gnu"
                        f"\n   - Or run with '--emit-c' to generate universal C source for the target OS."
                    )
                raise BuildError(
                    f"Compilation failed (exit code {result.returncode}):\n{err_msg}"
                )

            # Mark executable on POSIX if compiling for Unix-like host
            if sys.platform != "win32" and not (target_triple and "windows" in target_triple) and os.path.exists(target_binary):
                try:
                    os.chmod(target_binary, 0o755)
                except OSError:
                    pass

            file_size = os.path.getsize(target_binary)
            target_desc = target_triple or "c_binary"
            return BuildResult(
                success=True,
                source_path=source_path,
                output_path=target_binary,
                binary_size_bytes=file_size,
                bytecode_len=len(flat_inst),
                num_consts_len=len(num_consts),
                str_consts_len=len(str_consts),
                compiler_used=f"{os.path.basename(compiler_path)} ({compiler_type} -> {target_desc})",
                target=target_desc
            )
        finally:
            if os.path.exists(temp_c_path):
                os.remove(temp_c_path)


def build_standalone_binary(
    source_path: str,
    output_path: Optional[str] = None,
    emit_c: bool = False,
    emit_llvm: bool = False,
    target: Optional[str] = None,
    opt_level: str = "2",
    raylib: bool = False,
    verbose: bool = False
) -> str:
    """
    Convenience function to compile a .fox source file into a native binary executable or LLVM IR.
    Returns the absolute path to the generated binary, LLVM IR, or C source.
    """
    compiler = StandaloneCompiler()
    result = compiler.build(
        source_path=source_path,
        output_path=output_path,
        emit_c=emit_c,
        emit_llvm=emit_llvm,
        target=target,
        opt_level=opt_level,
        raylib=raylib,
        verbose=verbose
    )
    return os.path.abspath(result.output_path)

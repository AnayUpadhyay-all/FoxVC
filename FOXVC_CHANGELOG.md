# FoxVC Changelog

## [0.6.0-alpha] - Milestone 2 Engineering Stabilization

### Added
- **M2.1 Fuse Hybrid Module System:**
  - Implemented centralized module resolver (`engine/modules.py`) with canonical path resolution and search path prioritization.
  - Implemented module-local namespace isolation: imported modules execute in an isolated environment without polluting importer globals.
  - Controlled exports: modules explicitly expose public interfaces using top-level `emit` (`emit pack { ... }` or `emit <name>`); unexported symbols remain private.
  - Added module identity caching and circular-import cycle detection (`A -> B -> A`).
  - Extended `fuse` grammar in `engine/parser.py` to support relative and canonical string paths (`fuse "./utils/helper"`).
  - Unified module loading across Tree-Walking Interpreter and Python VM (`FoxVM`).
- **M2.2 Standard Library Modularization:**
  - Refactored `engine/shelf.py` into maintainable domain packages under `engine/shelves/`: `math.py`, `graphics.py`, `file.py`, `crypto.py`, `net.py`, `db.py`, `system.py`, and `compatibility.py`.
  - Added lazy loading for Raylib 2D hardware graphics to ensure headless environments do not load ctypes or shared libraries unnecessarily.
  - Preserved `engine/shelf.py` as a 100% backward-compatible facade re-exporting `get_standard_shelf()`, `SecurityPolicy`, and all builtins.
- **M2.3 Parser Reliability & Structured Diagnostics:**
  - Eliminated class-level mutable `ParserError.SOURCE_LINES` state, moving source lines and coordinates to instance-level fields.
  - Implemented 4-space tab expansion and unindent alignment validation in `engine/lexer.py`.
  - Added source-aware error reporting for `say` statements with comma expressions.
  - Added structured `Diagnostic` objects to `ExecutionResult.diagnostics` across all execution paths.
- **M2.4 Execution Engine Consistency & Opcode Disambiguation:**
  - Disambiguated overlapping opcode numbers for lists (`BUILD_LIST`: 28, `GET_INDEX`: 29, `SET_INDEX`: 30) from deprecated pack opcodes in Native C VM (`FoxCVM`).
  - Documented engine capability boundaries across Interpreter, Python VM, and Native C VM with differential testing coverage.
- **M2.5 Fox Den Studio Architecture:**
  - Decoupled headless execution and diagnostic services (`studio/services.py`) from GUI code.
  - Guarded Tkinter imports in `studio/app.py` and `studio/__init__.py` to allow headless operation in non-GUI environments.
  - Resolved `profile` keyword mismatch in `studio/web_engine.py` by aligning with the core `run_foxvc` contract.
- **M2.6 Security & Runtime Hardening:**
  - Implemented execution timeout enforcement via cooperative loop stepping and threaded execution deadlines.
  - Hardened filesystem sandbox with symlink-aware canonical checks (`os.path.realpath`).
  - Blocked loopback and private RFC 1918 network access for sandboxed HTTP requests.
  - Blocked `ATTACH DATABASE` and URI escapes in sandboxed SQLite queries.
  - Enforced missing-Origin rejection (HTTP 403) on Web Studio `/api/run`.
  - Bounded background concurrency (`spawn()`) to 64 concurrent tasks.
  - Validated fixed register and variable limits in Native C VM.
- **M2.7 Standalone Native Binary Compiler (`foxvc build`):**
  - Implemented `engine/builder.py` providing `StandaloneCompiler` and `build_standalone_binary()`.
  - Packages `.fox` source code, bytecode, and a tiny embedded C runner into a single standalone executable binary with zero Python or host dependencies.
  - Automatically discovers system C compilers (`gcc`, `clang`, `cl`).
  - Produces ultra-compact (~14KB) native ELF / PE / Mach-O executables.
  - Added support for `--emit-c` to export clean, inspectable standalone C source.
  - Added compiler optimization level flags (`-O 2`, `-O 3`, `-O s`).
  - Added `--raylib` flag for hardware-accelerated 2D game compilation.
  - Integrated `foxvc build <file.fox> [-o bin] [--emit-c]` into the CLI.
- **Decoupled Versioning Architecture:**
  - Created authoritative `engine/version.py` defining Language Version (`1.0.0`) and Engine Version (`0.6.0-alpha`).
  - Unified version metadata across CLI, Runtime, setup.py, and Studio.

---

## [0.3.4] - 2026-09-02
### Changed
- Eliminated static render dependency in FoxVC Web Runtime.
- Added native `mount <target>` and `show <target>` statements.

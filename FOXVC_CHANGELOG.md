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

## [0.6.0-alpha] - 2026-11-04
### Added
- **Developer Tooling CLI Suite:**
  - `foxvc fmt <path> [-w / --write] [-c / --check]`: Canonical auto-formatter enforcing 4-space indentation and binary operator spacing while strictly preserving string literals.
  - `foxvc lint <path> [--strict]`: Static code analyzer checking for unmutated `shift` variables, unread identifiers, dead code after `emit`/`halt`, and locked mutations.
  - `foxvc test [dir]`: Native automated test runner executing `.fox` test suites and `act test_*()` functions with sub-millisecond execution timing.
  - `foxvc lsp`: Full Language Server Protocol daemon speaking JSON-RPC 2.0 over stdin/stdout with real-time diagnostics, autocompletion for 25 keywords and shelves, and hover documentation.
- **CVM 2.0 Native Object/Struct Parity:**
  - Added native C struct and object member support (`Op.BUILD_PACK: 36`, `Op.GET_MEMBER: 37`, `Op.SET_MEMBER: 38`) allocated on the 8MB linear memory arena in `foxvm.c`.
  - Added hardware assertion opcode (`Op.GUARD: 35`) directly inside the C dispatch loop.
- **Expanded Standard Library Shelves:**
  - `engine/shelves/data.py`: Native parsing and serialization for JSON, CSV, TOML, Base64, and Hex encoding.
  - `engine/shelves/audio.py`: Native PCM sine wave sound synthesis, standard 16-bit Mono WAV file saving, tone playback, and Raylib audio hooks.
  - `engine/shelves/socket.py`: Raw TCP client/server, UDP datagrams, and RFC-6455 WebSocket frame encoding/decoding.
- **In-Browser WebAssembly Playground (`docs/`):**
  - Standalone client-side WASM playground hosted on GitHub Pages with CodeMirror editor and live sharing.
  - Interactive 60 FPS HTML5 Canvas 3D rotating geometry stage.
  - Smart Native Engine Detection triggering 1-click install guidance when backend servers or hardware features are invoked.
- **Visual Studio Code & Cursor Extension (`extensions/foxvc-vscode/`):**
  - Complete TextMate grammar (`foxvc.tmLanguage.json`), language configuration, and commands wired to `foxvc run`, `foxvc build`, `foxvc fmt`, and `foxvc test`.
- **Packaging:**
  - Standardized modern `pyproject.toml` and `setup.py` for PyPI distribution and `pip install .`.

---

## [0.3.4] - 2026-09-02
### Changed
- Eliminated static render dependency in FoxVC Web Runtime.
- Added native `mount <target>` and `show <target>` statements.

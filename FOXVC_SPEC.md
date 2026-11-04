# FoxVC Language & Runtime Specification

**Language Specification Version:** 1.0.0  
**Runtime Engine Version:** 0.6.0-alpha

---

## 1. Core Language Identity & Keyword Discipline

FoxVC enforces an exact 25-keyword lexicon with zero aliases or competitor overlap:
```text
act emit pack mold pick alt otherwise pulse cycle spin halt skip say ask guard trap fuse lock shift blank aye nay also either deny
```

* **Official Extension:** `.fox`
* **Boolean Literals:** `aye` (true), `nay` (false), `blank` (null/none)
* **Logical Operators:** `also` (logical AND with short-circuit), `either` (logical OR with short-circuit), `deny` (unary logical NOT)
* **Control Flow:** `pick ... alt ... otherwise` (conditionals), `spin` (while loop), `cycle` (counted range loop), `pulse` (delta-time continuous loop), `halt` (break), `skip` (continue)
* **Subroutines & Blueprints:** `act` (function declaration), `emit` (value return / module export), `mold` (object/type schema)
* **Defensive Coding:** `guard` (assertion with early exit), `trap ... otherwise` (exception catching and isolation)

---

## 2. Decoupled Versioning Architecture

FoxVC strictly decouples language specification semantics from runtime engine releases:
* **Language Version (`1.0.0`):** Authoritative specification of keywords, grammar, and AST behavior.
* **Engine Version (`0.6.0-alpha`):** Host engine implementation version across interpreters, compilers, and Studio.
The language version does not advance merely because engine internals change.

---

## 3. Fuse Hybrid Module System

FoxVC implements a hybrid module architecture combining module-local namespace isolation with explicit, controlled exports:

### 3.1 Module Resolution
* Modules are imported via `fuse <identifier>` or `fuse "<relative-or-canonical-path>"`.
* Canonical resolution uses symlink-aware realpaths (`os.path.realpath`).
* Search order:
  1. Directory of the importing file (for relative imports `./` or `../`).
  2. Current workspace / project root.
  3. Configured search paths.
* Supported file patterns: `<name>`, `<name>.fox`, and `<name>/main.fox`.

### 3.2 Namespace Isolation & Controlled Exports
* **Module-Local Namespace:** Every module executes in its own isolated environment. Top-level variables, functions, and blueprints inside a module do not pollute the importer's global environment.
* **Namespace Binding:** Imported modules are bound to their base identifier in the importer (`fuse "./utils/math"` binds to `math`).
* **Controlled Exports via `emit`:** Internal definitions remain private by default. A module explicitly exports its public interface using top-level `emit`:
  ```fox
  act add(a, b)
      emit a + b

  emit pack {
      add: add
  }
  ```
* **Member Access:** Callers invoke exported acts via member access: `math.add(10, 20)`. Accessing unexported private identifiers is rejected with a runtime error.
* **Cycle Detection:** Recursive circular imports (`A -> B -> A`) are detected dynamically and safely rejected before execution deadlocks.
* **Single Execution:** Modules are cached by their canonical identity and executed only once.

---

## 4. Standard Library Modularization (`engine/shelves/`)

The standard library is organized into domain-specific shelves with lazy loading and a unified compatibility facade:

* `engine/shelves/common.py`: Universal collections (`pack`, `push`, `pop`, `remove_at`, `len`), conversion helpers, and `SecurityPolicy`.
* `engine/shelves/math.py`: Trigonometry (`sin`, `cos`, `tan`), arithmetic primitives (`sqrt`, `floor`, `ceil`, `abs`, `round`, `pi`), game math (`clamp`, `lerp`, `distance`, `rectCollides`, `circleCollides`, `pointInRect`, `random`, `randomInt`, `randomChoice`).
* `engine/shelves/graphics.py`: Raylib 2D hardware windowing and input (`openWindow`, `closeWindow`, `startFrame`, `endFrame`, `drawBox`, `drawCircle`, `drawLine`, `drawText`, `isKeyDown`, `mouseX`, `mouseY`, `mouseDown`). **Graphics initialization is strictly lazy**, loading native libraries only upon invocation.
* `engine/shelves/file.py`: Filesystem I/O (`readFile`, `writeFile`, `appendFile`, `fileExists`, `removeFile`, `listDir`, `makeDir`, `removeDir`, `absPath`, `fileSize`), JSON serialization (`jsonParse`, `jsonString`), and string utilities (`split`, `join`, `trim`, `replace`, `upper`, `lower`, `contains`, `startsWith`, `endsWith`).
* `engine/shelves/crypto.py`: Hashing (`hashSha256`, `hashSha512`, `hashMd5`, `hmacSha256`), token and UUID generation (`uuid`, `secureToken`), and binary encoders (`base64Encode`, `base64Decode`, `hexEncode`, `hexDecode`).
* `engine/shelves/net.py`: REST client (`httpGet`, `httpPost`, `httpPut`, `httpDelete`, `fetch`, `urlEncode`, `urlDecode`) and microservice HTTP server (`httpServer`, `httpRoute`, `httpResponse`, `httpStart`, `httpStop`).
* `engine/shelves/db.py`: Embedded SQLite database (`dbOpen`, `dbExecute`, `dbQuery`, `dbClose`).
* `engine/shelves/system.py`: Environment (`getEnv`, `setEnv`, `listEnv`, `execCmd`, `platform`, `cpuCount`), clock (`time`, `sleep`), and bounded background concurrency (`spawn`, `awaitTask`).
* `engine/shelves/compatibility.py`: Stable facade assembling `get_standard_shelf()`.

---

## 5. Execution Engine Capability Matrix

FoxVC supports three execution engines with honest, documented capability boundaries:

| Feature / Subsystem | Tree-Walking Interpreter (`interp`) | Python Register VM (`vm`) | Native C VM (`fast`) |
| :--- | :---: | :---: | :---: |
| **Arithmetic & Logic** | Supported | Supported | Supported |
| **Control Flow (`pick`, `cycle`, `spin`)** | Supported | Supported | Supported |
| **Dynamic Acts & Recursion** | Supported | Supported | FoxVM fallback |
| **Numeric Arrays / Lists** | Supported | Supported | Supported (Opcode 28/29/30) |
| **Named Packs & Blueprints (`mold`)** | Supported | Supported | FoxVM fallback |
| **Trap & Guard Isolation** | Supported | Supported | FoxVM fallback |
| **Fuse Module System** | Supported | Supported | FoxVM fallback |
| **Raylib 2D Hardware Graphics** | Supported | Supported | Supported (Native FFI) |
| **SQLite, Crypto, Network Shelves** | Supported | Supported | FoxVM fallback |

When `engine_mode='fast'` encounters dynamic acts, molds, or modules without `allow_fallback=True`, it cleanly rejects execution with a `NotImplementedError` rather than silently degrading or miscomputing results.

---

## 6. Security and Containment Controls

* **Execution Timeout:** Enforces execution deadlines both cooperatively within loop boundaries and externally via thread execution limits.
* **Filesystem Sandbox:** Resolves target paths using canonical symlink resolution (`os.path.realpath`). Operations escaping the approved directory via relative traversal or symlinks are blocked.
* **Network Isolation:** In sandboxed mode, outbound HTTP requests targeting loopback addresses (`127.0.0.1`, `localhost`) or private RFC 1918 subnets are rejected. TLS verification is enforced by default.
* **SQLite Hardening:** Database connections in sandboxed mode enforce `uri=False` and block `ATTACH DATABASE` directives.
* **Web Studio Security:** Restricts `/api/run` to explicit loopback origins; requests with missing or untrusted `Origin` headers are rejected with HTTP 403 Forbidden.
* **Concurrency Bounds:** Spawning background tasks via `spawn()` is capped at 64 concurrent tasks to prevent resource exhaustion.
* **C VM Limits:** Validates fixed-size limits (registers ≤ 256, variables ≤ 512, arena ≤ 8MB) prior to native dispatch.

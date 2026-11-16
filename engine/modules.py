"""
FoxVC Centralized Module System (v0.6.0-alpha).
Implements the hybrid module architecture:
- Centralized module resolver with canonical path canonicalization
- Relative and search-path resolution
- Module identity, caching, and duplicate execution protection
- Circular-import detection
- Module-local isolated environments
- Explicit exports via top-level 'emit'
"""

import os
from typing import Dict, Any, List, Optional, Set, Callable
from engine.runtime import FoxPack


class ModuleError(RuntimeError):
    """Raised when module resolution, loading, or circular import errors occur."""
    def __init__(self, message: str, line: int = 1, column: int = 1, file: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.file = file


class ModuleResolver:
    """Resolves relative and package module specifiers to canonical filesystem paths."""
    def __init__(self, search_paths: Optional[List[str]] = None):
        self.search_paths: List[str] = [os.path.abspath(p) for p in search_paths] if search_paths else []

    def resolve(self, module_spec: str, importing_file: Optional[str] = None) -> str:
        """
        Resolves a module specifier to a canonical realpath.
        Supports:
        - Relative imports: './foo', '../bar'
        - Direct file names: 'math.fox', 'math'
        - Subdirectory modules: 'utils/helper'
        """
        spec = str(module_spec).strip()
        candidates = []

        # Determine caller directory
        caller_dir = None
        if importing_file:
            importing_file_abs = os.path.abspath(importing_file)
            caller_dir = os.path.dirname(importing_file_abs)

        # 1. Check relative imports (starts with . or ..)
        if spec.startswith("./") or spec.startswith("../"):
            base_dir = caller_dir if caller_dir else os.getcwd()
            rel_target = os.path.join(base_dir, spec)
            candidates.append(rel_target)
        else:
            # 2. Check caller directory first (if available)
            if caller_dir:
                candidates.append(os.path.join(caller_dir, spec))

            # 3. Check current working directory
            candidates.append(os.path.join(os.getcwd(), spec))

            # 4. Check configured search paths
            for sp in self.search_paths:
                candidates.append(os.path.join(sp, spec))

        # Test candidate extensions
        checked = []
        for cand in candidates:
            # Exact path
            checked.append(cand)
            if os.path.isfile(cand):
                return os.path.realpath(cand)

            # Append .fox
            cand_fox = f"{cand}.fox" if not cand.endswith(".fox") else cand
            checked.append(cand_fox)
            if os.path.isfile(cand_fox):
                return os.path.realpath(cand_fox)

            # Check directory module (cand/main.fox)
            cand_main = os.path.join(cand, "main.fox")
            checked.append(cand_main)
            if os.path.isfile(cand_main):
                return os.path.realpath(cand_main)

        raise ModuleError(
            f"Cannot resolve module '{spec}'. Searched locations:\n" +
            "\n".join(f"  - {c}" for c in checked[:8]),
            file=importing_file
        )


class ModuleManager:
    """Authoritative module cache, cycle detector, and isolated executor."""
    def __init__(self, resolver: Optional[ModuleResolver] = None):
        self.resolver = resolver or ModuleResolver()
        self.loaded_modules: Dict[str, FoxPack] = {}
        self.loading_stack: List[str] = []

    def get_canonical_id(self, module_spec: str, importing_file: Optional[str] = None) -> str:
        return self.resolver.resolve(module_spec, importing_file)

    def load_module(
        self,
        module_spec: str,
        importing_file: Optional[str] = None,
        sandboxed: bool = False,
        allowed_dir: Optional[str] = None,
        security_policy: Any = None,
        line: int = 1,
        column: int = 1
    ) -> FoxPack:
        """
        Loads a module within an isolated execution environment, enforcing:
        - Canonical identity and caching
        - Duplicate execution avoidance
        - Circular-import detection
        - Explicit export filtering (controlled exports)
        """
        spec = str(module_spec).strip()
        from engine.shelves import (
            get_math_shelf, get_graphics_shelf, get_file_shelf, get_crypto_shelf,
            get_net_shelf, get_db_shelf, get_system_shelf, get_data_shelf,
            get_audio_shelf, get_socket_shelf, get_text_shelf
        )
        builtin_shelves = {
            "math": lambda: get_math_shelf(),
            "graphics": lambda: get_graphics_shelf(),
            "file": lambda: get_file_shelf(security_policy),
            "crypto": lambda: get_crypto_shelf(),
            "net": lambda: get_net_shelf(security_policy),
            "db": lambda: get_db_shelf(security_policy),
            "system": lambda: get_system_shelf(security_policy),
            "data": lambda: get_data_shelf(security_policy),
            "audio": lambda: get_audio_shelf(security_policy),
            "socket": lambda: get_socket_shelf(security_policy),
            "text": lambda: get_text_shelf(),
        }
        if spec in builtin_shelves:
            shelf_dict = builtin_shelves[spec]()
            pack = FoxPack(shelf_dict)
            self.loaded_modules[spec] = pack
            return pack

        try:
            canonical_path = self.resolver.resolve(module_spec, importing_file)
        except ModuleError as me:
            me.line = line
            me.column = column
            me.file = importing_file
            raise me

        # Security check: if sandboxed, module must be inside allowed_dir
        if security_policy and security_policy.sandboxed:
            target = security_policy.resolve_path(canonical_path)
            if target is None:
                raise ModuleError(
                    f"PermissionDenied: Module '{module_spec}' is outside the sandboxed directory",
                    line=line, column=column, file=importing_file
                )
            canonical_path = target

        # Cache check
        if canonical_path in self.loaded_modules:
            return self.loaded_modules[canonical_path]

        # Circular import check
        if canonical_path in self.loading_stack:
            cycle_chain = " -> ".join([os.path.basename(p) for p in self.loading_stack] + [os.path.basename(canonical_path)])
            raise ModuleError(
                f"Circular import detected: {cycle_chain}",
                line=line, column=column, file=importing_file
            )

        self.loading_stack.append(canonical_path)

        try:
            with open(canonical_path, "r", encoding="utf-8") as f:
                source = f.read()

            from engine.lexer import Lexer
            from engine.parser import Parser
            from engine.interpreter import Interpreter, EmitSignal

            tokens = Lexer(source, filename=canonical_path).tokenize()
            ast = Parser(tokens, filename=canonical_path, source=source).parse()

            # Execute in an isolated interpreter instance sharing the module manager
            mod_interp = Interpreter(
                policy=security_policy,
                sandboxed=sandboxed,
                allowed_dir=allowed_dir,
                filename=canonical_path
            )
            # Share the module cache so nested imports reuse cached modules
            mod_interp.module_manager = self

            emitted_val = None
            try:
                mod_interp.execute(ast)
                emitted_val = getattr(mod_interp, "last_emitted", None)
            except EmitSignal as es:
                emitted_val = es.value

            # Determine public exports
            exported_pack = self._build_exports(emitted_val, mod_interp)
            self.loaded_modules[canonical_path] = exported_pack
            return exported_pack

        finally:
            if self.loading_stack and self.loading_stack[-1] == canonical_path:
                self.loading_stack.pop()

    def _build_exports(self, emitted_val: Any, interp: Any) -> FoxPack:
        """
        Builds the public module namespace.
        If the module executed an explicit top-level 'emit':
        - If a FoxPack: only the keys in that pack are public.
        - If a dictionary: FoxPack(dict)
        - If a callable or single value: packed with its symbol name or 'default'
        If no explicit emit was performed:
        - Internal definitions remain private (empty FoxPack).
        """
        if emitted_val is not None:
            if isinstance(emitted_val, FoxPack):
                return emitted_val
            if isinstance(emitted_val, dict):
                return FoxPack(emitted_val)
            if isinstance(emitted_val, (list, tuple)):
                pack_dict = {}
                for item in emitted_val:
                    name = getattr(item, "__name__", None)
                    if name:
                        pack_dict[name] = item
                if pack_dict:
                    return FoxPack(pack_dict)
                return FoxPack({"exports": list(emitted_val)})
            # Single value or act
            name = getattr(emitted_val, "__name__", "value")
            return FoxPack({name: emitted_val})

        # No explicit emit: definitions are private by default
        return FoxPack({})

"""
Common collection primitives, conversion utilities, and security policies for FoxVC shelves.
"""

import os
from typing import Dict, Any, List, Optional
from engine.runtime import FoxPack


def to_fox_val(val: Any) -> Any:
    if isinstance(val, dict):
        return FoxPack({k: to_fox_val(v) for k, v in val.items()})
    elif isinstance(val, list):
        return [to_fox_val(x) for x in val]
    return val


def _clean_obj(o: Any) -> Any:
    if hasattr(o, "_data"):
        return {k: _clean_obj(v) for k, v in o._data.items()}
    if isinstance(o, list):
        return [_clean_obj(x) for x in o]
    return o


def fox_pack(*args) -> Any:
    """Dynamic list constructor: pack() or pack(initial_cap) or pack(*elements)."""
    if len(args) == 0:
        return []
    if len(args) == 1 and isinstance(args[0], (int, float)):
        return [0.0] * int(args[0])
    return list(args)


def fox_push(lst: Any, item: Any) -> Any:
    if isinstance(lst, list):
        lst.append(item)
    return lst


def fox_pop(lst: Any) -> Any:
    if isinstance(lst, list) and len(lst) > 0:
        return lst.pop()
    return 0


def fox_remove_at(lst: Any, idx: Any) -> Any:
    if isinstance(lst, list) and 0 <= int(idx) < len(lst):
        return lst.pop(int(idx))
    return 0


class SecurityPolicy:
    """Explicit security execution boundary with canonical, symlink-aware verification."""
    def __init__(self, sandboxed: bool = False, allowed_dir: Optional[str] = None):
        self.sandboxed = sandboxed
        self.allowed_dir = os.path.realpath(os.path.abspath(allowed_dir)) if allowed_dir else None
        self.isolated_env: Dict[str, str] = {}

    def resolve_path(self, path: Any) -> Optional[str]:
        path_str = str(path)
        if not self.sandboxed:
            return os.path.abspath(path_str)
        if not self.allowed_dir:
            return None

        # Build tentative path inside allowed_dir
        if os.path.isabs(path_str):
            candidate = os.path.abspath(path_str)
        else:
            candidate = os.path.abspath(os.path.join(self.allowed_dir, path_str))

        # Canonicalize resolving symlinks
        canonical_target = os.path.realpath(candidate)
        canonical_allowed = self.allowed_dir

        try:
            # Must be inside canonical_allowed and not equal to removing the root
            common = os.path.commonpath([canonical_target, canonical_allowed])
            if common == canonical_allowed:
                return canonical_target
        except Exception:
            pass
        return None

"""
FoxVC Universal Standard Shelf Compatibility Facade.
Aggregates all domain shelves into the unified standard shelf environment.
"""

from typing import Dict, Any, Optional
from .common import fox_pack, fox_push, fox_pop, fox_remove_at, SecurityPolicy
from .math import get_math_shelf
from .graphics import get_graphics_shelf
from .file import get_file_shelf
from .crypto import get_crypto_shelf
from .net import get_net_shelf
from .db import get_db_shelf
from .system import get_system_shelf
from .data import get_data_shelf
from .audio import get_audio_shelf
from .socket import get_socket_shelf


def get_standard_shelf(policy: Optional[SecurityPolicy] = None, sandboxed: bool = False, allowed_dir: Optional[str] = None) -> Dict[str, Any]:
    """Returns the unified standard shelf dictionary configured with the active security policy."""
    if policy is None:
        policy = SecurityPolicy(sandboxed=sandboxed, allowed_dir=allowed_dir)

    shelf: Dict[str, Any] = {
        # Universal collection primitives
        "pack": fox_pack,
        "push": fox_push,
        "pop": fox_pop,
        "remove_at": fox_remove_at,
        "len": len,
    }

    shelf.update(get_math_shelf())
    shelf.update(get_graphics_shelf())
    shelf.update(get_file_shelf(policy))
    shelf.update(get_crypto_shelf())
    shelf.update(get_net_shelf(policy))
    shelf.update(get_db_shelf(policy))
    shelf.update(get_system_shelf(policy))
    shelf.update(get_data_shelf(policy))
    shelf.update(get_audio_shelf(policy))
    shelf.update(get_socket_shelf(policy))

    return shelf

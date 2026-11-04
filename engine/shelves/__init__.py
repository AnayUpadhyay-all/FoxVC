"""
FoxVC Modular Shelves Architecture (v0.6.0-alpha).
Modular domain-specific standard libraries with lazy-loaded dependencies and unified compatibility facade.
"""

from .common import (
    SecurityPolicy,
    fox_pack,
    fox_push,
    fox_pop,
    fox_remove_at,
    to_fox_val,
    _clean_obj
)
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
from .compatibility import get_standard_shelf

__all__ = [
    "SecurityPolicy",
    "get_standard_shelf",
    "get_math_shelf",
    "get_graphics_shelf",
    "get_file_shelf",
    "get_crypto_shelf",
    "get_net_shelf",
    "get_db_shelf",
    "get_system_shelf",
    "get_data_shelf",
    "get_audio_shelf",
    "get_socket_shelf",
    "fox_pack",
    "fox_push",
    "fox_pop",
    "fox_remove_at",
    "to_fox_val",
    "_clean_obj"
]

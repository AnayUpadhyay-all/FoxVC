
# Universal Collection Primitives (General-Purpose, Zero Game Assumptions)
def fox_pack(*args):
    # Dynamic list constructor: pack() or pack(initial_cap)
    if len(args) == 0:
        return []
    if len(args) == 1 and isinstance(args[0], (int, float)):
        return [0.0] * int(args[0])
    return list(args)

def fox_push(lst, item):
    if isinstance(lst, list):
        lst.append(item)
    return lst

def fox_pop(lst):
    if isinstance(lst, list) and len(lst) > 0:
        return lst.pop()
    return 0

def fox_remove_at(lst, idx):
    if isinstance(lst, list) and 0 <= int(idx) < len(lst):
        return lst.pop(int(idx))
    return 0


def fox_get_mouse_x():
    if _raylib:
        return _raylib.GetMouseX()
    return 0

def fox_get_mouse_y():
    if _raylib:
        return _raylib.GetMouseY()
    return 0

def fox_mouse_down(btn=0):
    if _raylib:
        return 1 if _raylib.IsMouseButtonDown(int(btn)) else 0
    return 0


import ctypes
import os

# Load Native Raylib Shared Library
_lib_dir = os.path.join(os.path.dirname(__file__), "lib")
_libraylib_path = os.path.join(_lib_dir, "libraylib.so")
_raylib = None

try:
    _raylib = ctypes.CDLL(_libraylib_path, mode=ctypes.RTLD_GLOBAL)
    
    # Declare function prototypes
    _raylib.InitWindow.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
    _raylib.InitWindow.restype = None
    _raylib.SetTargetFPS.argtypes = [ctypes.c_int]
    _raylib.SetTargetFPS.restype = None
    _raylib.WindowShouldClose.argtypes = []
    _raylib.WindowShouldClose.restype = ctypes.c_bool
    _raylib.CloseWindow.argtypes = []
    _raylib.CloseWindow.restype = None
    _raylib.BeginDrawing.argtypes = []
    _raylib.BeginDrawing.restype = None
    _raylib.EndDrawing.argtypes = []
    _raylib.EndDrawing.restype = None
    _raylib.ClearBackground.argtypes = [ctypes.c_uint32]
    _raylib.ClearBackground.restype = None
    _raylib.DrawRectangle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    _raylib.DrawRectangle.restype = None
    _raylib.IsKeyDown.argtypes = [ctypes.c_int]
    _raylib.IsKeyDown.restype = ctypes.c_bool
except Exception as e:
    pass


def fox_close_window():
    if _raylib and _raylib.IsWindowReady():
        _raylib.CloseWindow()
    return 1

def fox_open_window(w, h, title="FoxVC Game"):
    if _raylib:
        _raylib.InitWindow(int(w), int(h), str(title).encode("utf-8"))
        _raylib.SetTargetFPS(60)
    return 1

def fox_window_closed():
    if _raylib:
        return 1 if _raylib.WindowShouldClose() else 0
    return 1

def fox_start_frame():
    if _raylib:
        _raylib.BeginDrawing()
        # 0xFF19120F = Dark slate background in RGBA/ABGR
        _raylib.ClearBackground(0xFF19120F)
    return 1

def fox_end_frame():
    if _raylib:
        _raylib.EndDrawing()
    return 1

def fox_draw_box(x, y, w, h, col=1):
    if _raylib:
        # Colors: 1 = Orange (0xFF00A5FF), 2 = Green (0xFF00E600), 3 = Red (0xFF0000FF), 0 = White (0xFFFFFFFF)
        c = 0xFF00A5FF
        if int(col) == 2:
            c = 0xFF00E600
        elif int(col) == 3:
            c = 0xFF0000FF
        elif int(col) == 0:
            c = 0xFFFFFFFF
        _raylib.DrawRectangle(int(x), int(y), int(w), int(h), c)
    return 1

def fox_is_key_down(key):
    if _raylib:
        return 1 if _raylib.IsKeyDown(int(key)) else 0
    return 0

"""
FoxVC Minimal Shelf (v0.5.2x)
Raw math and hardware clock primitives. Zero black-box libraries.
"""

import math
import time
from typing import Dict, Any


def get_standard_shelf() -> Dict[str, Any]:
    return {
        "pack": fox_pack,
        "push": fox_push,
        "pop": fox_pop,
        "remove_at": fox_remove_at,
        "mouseX": fox_get_mouse_x,
        "mouseY": fox_get_mouse_y,
        "mouseDown": fox_mouse_down,
        "openWindow": fox_open_window,
        "windowClosed": fox_window_closed,
        "closeWindow": fox_close_window,
        "startFrame": fox_start_frame,
        "endFrame": fox_end_frame,
        "drawBox": fox_draw_box,
        "isKeyDown": fox_is_key_down,
        # Constants
        "pi": math.pi,
        
        # Raw Math Primitives (Callable)
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "floor": math.floor,
        "ceil": math.ceil,
        "abs": abs,
        "round": round,
        
        # Clock Primitives
        "time": time.time,
        "sleep": time.sleep,
        "len": len,
    }

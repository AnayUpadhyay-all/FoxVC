
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
    _raylib.DrawCircle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_uint32]
    _raylib.DrawCircle.restype = None
    _raylib.DrawLine.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    _raylib.DrawLine.restype = None
    _raylib.DrawText.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
    _raylib.DrawText.restype = None
    _raylib.GetFPS.argtypes = []
    _raylib.GetFPS.restype = ctypes.c_int
    _raylib.IsKeyPressed.argtypes = [ctypes.c_int]
    _raylib.IsKeyPressed.restype = ctypes.c_bool
    _raylib.IsMouseButtonPressed.argtypes = [ctypes.c_int]
    _raylib.IsMouseButtonPressed.restype = ctypes.c_bool
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

def fox_draw_circle(cx, cy, radius, col=1):
    if _raylib:
        _raylib.DrawCircle(int(cx), int(cy), float(radius), _get_uint_color(col))
    return 1

def fox_draw_line(x1, y1, x2, y2, col=1):
    if _raylib:
        _raylib.DrawLine(int(x1), int(y1), int(x2), int(y2), _get_uint_color(col))
    return 1

def fox_draw_text(text, x, y, size=20, col=0):
    if _raylib:
        _raylib.DrawText(str(text).encode("utf-8"), int(x), int(y), int(size), _get_uint_color(col))
    return 1

def fox_get_fps():
    if _raylib:
        return _raylib.GetFPS()
    return 60

def fox_set_fps(fps):
    if _raylib:
        _raylib.SetTargetFPS(int(fps))
    return 1

def fox_is_key_pressed(key):
    if _raylib:
        return 1 if _raylib.IsKeyPressed(int(key)) else 0
    return 0

def fox_mouse_clicked(btn=0):
    if _raylib:
        return 1 if _raylib.IsMouseButtonPressed(int(btn)) else 0
    return 0

def _get_uint_color(col):
    colors = {
        0: 0xFFFFFFFF, # White
        1: 0xFF00A5FF, # Orange
        2: 0xFF00E600, # Green
        3: 0xFF0000FF, # Red
        4: 0xFFFF5500, # Blue
        5: 0xFF00E5FF, # Yellow
        6: 0xFFFF00CC, # Purple
        7: 0xFF000000, # Black
    }
    return colors.get(int(col), 0xFFFFFFFF)

# File System I/O
def fox_read_file(path):
    try:
        with open(str(path), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""

def fox_write_file(path, content):
    try:
        with open(str(path), "w", encoding="utf-8") as f:
            f.write(str(content))
        return 1
    except Exception:
        return 0

def fox_append_file(path, content):
    try:
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(str(content))
        return 1
    except Exception:
        return 0

def fox_file_exists(path):
    return 1 if os.path.exists(str(path)) else 0

def fox_remove_file(path):
    try:
        if os.path.exists(str(path)):
            os.remove(str(path))
            return 1
    except Exception:
        pass
    return 0

def fox_list_dir(path="."):
    try:
        return os.listdir(str(path))
    except Exception:
        return []

# JSON Data
def fox_json_parse(text):
    try:
        return json.loads(str(text))
    except Exception:
        return {}

def fox_json_string(obj, indent=0):
    try:
        def _clean(o):
            if hasattr(o, "_data"):
                return {k: _clean(v) for k, v in o._data.items()}
            if isinstance(o, list):
                return [_clean(x) for x in o]
            return o
        if indent > 0:
            return json.dumps(_clean(obj), indent=int(indent))
        return json.dumps(_clean(obj))
    except Exception:
        return "{}"

# String utilities
def fox_split(s, sep=" "):
    return str(s).split(str(sep))

def fox_join(sep, lst):
    if isinstance(lst, list):
        return str(sep).join(str(x) for x in lst)
    return str(lst)

def fox_trim(s):
    return str(s).strip()

def fox_replace(s, old, new):
    return str(s).replace(str(old), str(new))

def fox_upper(s):
    return str(s).upper()

def fox_lower(s):
    return str(s).lower()

def fox_contains(s, sub):
    return 1 if str(sub) in str(s) else 0

def fox_starts_with(s, prefix):
    return 1 if str(s).startswith(str(prefix)) else 0

def fox_ends_with(s, suffix):
    return 1 if str(s).endswith(str(suffix)) else 0

# Game Math, Physics & Collisions
def fox_clamp(val, min_v, max_v):
    return max(float(min_v), min(float(val), float(max_v)))

def fox_lerp(a, b, t):
    return float(a) + (float(b) - float(a)) * float(t)

def fox_distance(x1, y1, x2, y2):
    return math.hypot(float(x2) - float(x1), float(y2) - float(y1))

def fox_rect_collides(x1, y1, w1, h1, x2, y2, w2, h2):
    return 1 if (float(x1) < float(x2) + float(w2) and
                 float(x1) + float(w1) > float(x2) and
                 float(y1) < float(y2) + float(h2) and
                 float(y1) + float(h1) > float(y2)) else 0

def fox_circle_collides(x1, y1, r1, x2, y2, r2):
    d = math.hypot(float(x2) - float(x1), float(y2) - float(y1))
    return 1 if d < (float(r1) + float(r2)) else 0

def fox_point_in_rect(px, py, rx, ry, rw, rh):
    return 1 if (float(rx) <= float(px) <= float(rx) + float(rw) and
                 float(ry) <= float(py) <= float(ry) + float(rh)) else 0

def fox_random(min_v=0, max_v=1):
    return random.uniform(float(min_v), float(max_v))

def fox_random_int(min_v, max_v):
    return random.randint(int(min_v), int(max_v))

def fox_random_choice(lst):
    if isinstance(lst, list) and len(lst) > 0:
        return random.choice(lst)
    return 0

"""
FoxVC Standard Shelf
Comprehensive utilities for Games, Math, File System, JSON, and String Processing.
"""

import math
import time
import json
import random
from typing import Dict, Any


def get_standard_shelf() -> Dict[str, Any]:
    return {
        # Collection Primitives
        "pack": fox_pack,
        "push": fox_push,
        "pop": fox_pop,
        "remove_at": fox_remove_at,
        "len": len,

        # Hardware & Raylib 2D Graphics Engine
        "openWindow": fox_open_window,
        "windowClosed": fox_window_closed,
        "closeWindow": fox_close_window,
        "startFrame": fox_start_frame,
        "endFrame": fox_end_frame,
        "drawBox": fox_draw_box,
        "drawCircle": fox_draw_circle,
        "drawLine": fox_draw_line,
        "drawText": fox_draw_text,
        "getFPS": fox_get_fps,
        "setFPS": fox_set_fps,
        "isKeyDown": fox_is_key_down,
        "isKeyPressed": fox_is_key_pressed,
        "mouseX": fox_get_mouse_x,
        "mouseY": fox_get_mouse_y,
        "mouseDown": fox_mouse_down,
        "mouseClicked": fox_mouse_clicked,

        # File System I/O
        "readFile": fox_read_file,
        "writeFile": fox_write_file,
        "appendFile": fox_append_file,
        "fileExists": fox_file_exists,
        "removeFile": fox_remove_file,
        "listDir": fox_list_dir,

        # JSON Data Serialization
        "jsonParse": fox_json_parse,
        "jsonString": fox_json_string,

        # String Utilities
        "split": fox_split,
        "join": fox_join,
        "trim": fox_trim,
        "replace": fox_replace,
        "upper": fox_upper,
        "lower": fox_lower,
        "contains": fox_contains,
        "startsWith": fox_starts_with,
        "endsWith": fox_ends_with,

        # Game Math & Collision Primitives
        "clamp": fox_clamp,
        "lerp": fox_lerp,
        "distance": fox_distance,
        "rectCollides": fox_rect_collides,
        "circleCollides": fox_circle_collides,
        "pointInRect": fox_point_in_rect,
        "random": fox_random,
        "randomInt": fox_random_int,
        "randomChoice": fox_random_choice,

        # Raw Math Primitives
        "pi": math.pi,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "floor": math.floor,
        "ceil": math.ceil,
        "abs": abs,
        "round": round,

        # Clock & System
        "time": time.time,
        "sleep": time.sleep,
    }

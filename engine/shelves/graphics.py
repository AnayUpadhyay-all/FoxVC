"""
FoxVC 2D Graphics and Hardware Shelf.
Provides lazy-loaded Raylib window management, drawing primitives, and user input polling.
"""

import os
from typing import Dict, Any, Optional

_raylib = None
_raylib_attempted = False


def _get_raylib():
    """Lazily load Raylib shared library only when graphics functions are invoked."""
    global _raylib, _raylib_attempted
    if _raylib_attempted:
        return _raylib
    _raylib_attempted = True

    try:
        import ctypes
        engine_dir = os.path.dirname(os.path.dirname(__file__))
        libraylib_path = os.path.join(engine_dir, "lib", "libraylib.so")
        if not os.path.exists(libraylib_path):
            return None

        rl = ctypes.CDLL(libraylib_path, mode=ctypes.RTLD_GLOBAL)
        
        # Function prototypes
        rl.InitWindow.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
        rl.InitWindow.restype = None
        rl.SetTargetFPS.argtypes = [ctypes.c_int]
        rl.SetTargetFPS.restype = None
        rl.WindowShouldClose.argtypes = []
        rl.WindowShouldClose.restype = ctypes.c_bool
        rl.CloseWindow.argtypes = []
        rl.CloseWindow.restype = None
        rl.BeginDrawing.argtypes = []
        rl.BeginDrawing.restype = None
        rl.EndDrawing.argtypes = []
        rl.EndDrawing.restype = None
        rl.ClearBackground.argtypes = [ctypes.c_uint32]
        rl.ClearBackground.restype = None
        rl.DrawRectangle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        rl.DrawRectangle.restype = None
        rl.IsKeyDown.argtypes = [ctypes.c_int]
        rl.IsKeyDown.restype = ctypes.c_bool
        rl.DrawCircle.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_float, ctypes.c_uint32]
        rl.DrawCircle.restype = None
        rl.DrawLine.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        rl.DrawLine.restype = None
        rl.DrawText.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint32]
        rl.DrawText.restype = None
        rl.GetFPS.argtypes = []
        rl.GetFPS.restype = ctypes.c_int
        rl.IsKeyPressed.argtypes = [ctypes.c_int]
        rl.IsKeyPressed.restype = ctypes.c_bool
        rl.IsMouseButtonPressed.argtypes = [ctypes.c_int]
        rl.IsMouseButtonPressed.restype = ctypes.c_bool
        rl.GetMouseX.argtypes = []
        rl.GetMouseX.restype = ctypes.c_int
        rl.GetMouseY.argtypes = []
        rl.GetMouseY.restype = ctypes.c_int
        rl.IsMouseButtonDown.argtypes = [ctypes.c_int]
        rl.IsMouseButtonDown.restype = ctypes.c_bool

        _raylib = rl
        return _raylib
    except Exception:
        return None


def _get_uint_color(col):
    colors = {
        0: 0xFFFFFFFF,  # White
        1: 0xFF00A5FF,  # Orange
        2: 0xFF00E600,  # Green
        3: 0xFF0000FF,  # Red
        4: 0xFFFF5500,  # Blue
        5: 0xFF00E5FF,  # Yellow
        6: 0xFFFF00CC,  # Purple
        7: 0xFF000000,  # Black
    }
    return colors.get(int(col), 0xFFFFFFFF)


def fox_open_window(w, h, title="FoxVC Game"):
    rl = _get_raylib()
    if rl:
        rl.InitWindow(int(w), int(h), str(title).encode("utf-8"))
        rl.SetTargetFPS(60)
    return 1


def fox_close_window():
    rl = _get_raylib()
    if rl:
        try:
            rl.CloseWindow()
        except Exception:
            pass
    return 1


def fox_window_closed():
    rl = _get_raylib()
    if rl:
        return 1 if rl.WindowShouldClose() else 0
    return 1


def fox_start_frame():
    rl = _get_raylib()
    if rl:
        rl.BeginDrawing()
        rl.ClearBackground(0xFF19120F)
    return 1


def fox_end_frame():
    rl = _get_raylib()
    if rl:
        rl.EndDrawing()
    return 1


def fox_draw_box(x, y, w, h, col=1):
    rl = _get_raylib()
    if rl:
        c = 0xFF00A5FF
        if int(col) == 2:
            c = 0xFF00E600
        elif int(col) == 3:
            c = 0xFF0000FF
        elif int(col) == 0:
            c = 0xFFFFFFFF
        rl.DrawRectangle(int(x), int(y), int(w), int(h), c)
    return 1


def fox_draw_circle(cx, cy, radius, col=1):
    rl = _get_raylib()
    if rl:
        rl.DrawCircle(int(cx), int(cy), float(radius), _get_uint_color(col))
    return 1


def fox_draw_line(x1, y1, x2, y2, col=1):
    rl = _get_raylib()
    if rl:
        rl.DrawLine(int(x1), int(y1), int(x2), int(y2), _get_uint_color(col))
    return 1


def fox_draw_text(text, x, y, size=20, col=0):
    rl = _get_raylib()
    if rl:
        rl.DrawText(str(text).encode("utf-8"), int(x), int(y), int(size), _get_uint_color(col))
    return 1


def fox_get_fps():
    rl = _get_raylib()
    if rl:
        return rl.GetFPS()
    return 60


def fox_set_fps(fps):
    rl = _get_raylib()
    if rl:
        rl.SetTargetFPS(int(fps))
    return 1


def fox_is_key_down(key):
    rl = _get_raylib()
    if rl:
        return 1 if rl.IsKeyDown(int(key)) else 0
    return 0


def fox_is_key_pressed(key):
    rl = _get_raylib()
    if rl:
        return 1 if rl.IsKeyPressed(int(key)) else 0
    return 0


def fox_get_mouse_x():
    rl = _get_raylib()
    if rl:
        return rl.GetMouseX()
    return 0


def fox_get_mouse_y():
    rl = _get_raylib()
    if rl:
        return rl.GetMouseY()
    return 0


def fox_mouse_down(btn=0):
    rl = _get_raylib()
    if rl:
        return 1 if rl.IsMouseButtonDown(int(btn)) else 0
    return 0


def fox_mouse_clicked(btn=0):
    rl = _get_raylib()
    if rl:
        return 1 if rl.IsMouseButtonPressed(int(btn)) else 0
    return 0


def get_graphics_shelf() -> Dict[str, Any]:
    return {
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
    }

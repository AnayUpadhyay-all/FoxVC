"""
FoxVC Math & Physics Shelf.
Contains core math constants, trigonometry, interpolation, and collision helpers.
"""

import math
import random
from typing import Dict, Any, List


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


def get_math_shelf() -> Dict[str, Any]:
    return {
        "pi": math.pi,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "sqrt": math.sqrt,
        "floor": math.floor,
        "ceil": math.ceil,
        "abs": abs,
        "round": round,
        "clamp": fox_clamp,
        "lerp": fox_lerp,
        "distance": fox_distance,
        "rectCollides": fox_rect_collides,
        "circleCollides": fox_circle_collides,
        "pointInRect": fox_point_in_rect,
        "random": fox_random,
        "randomInt": fox_random_int,
        "randomChoice": fox_random_choice,
    }

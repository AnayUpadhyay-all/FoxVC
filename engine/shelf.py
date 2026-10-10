"""
FoxVC Minimal Shelf (v0.5.2x)
Raw math and hardware clock primitives. Zero black-box libraries.
"""

import math
import time
from typing import Dict, Any


def get_standard_shelf() -> Dict[str, Any]:
    return {
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

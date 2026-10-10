"""
FoxVC Client-Side WebAssembly Worker Engine
Executed entirely inside client browsers via Pyodide.
Consumes client mobile CPU/GPU exclusively.
"""

import json
from engine.runner import run_foxvc

def execute_foxvc_source(source_code: str, profile: str = "complex") -> str:
    res = run_foxvc(source_code, profile=profile)
    if not res.success:
        return json.dumps({
            "success": False,
            "error": res.error,
            "entities": [],
            "connectors": [],
            "background": "#080B12"
        })

    scene = res.spatial_space
    if not scene:
        return json.dumps({
            "success": True,
            "output": res.output,
            "is_spatial": False,
            "background": "#080B12"
        })

    # Export structural metadata for phone GPU canvas loop
    entities_data = []
    for name in scene.ordered_dependencies:
        e = scene.entities[name]
        entities_data.append({
            "name": e.name,
            "form": e.form_kind,
            "width": e.resolved_width,
            "height": e.resolved_height,
            "fill": str(e.get_property("fill", "#E2E8F0")),
            "stroke": str(e.get_property("stroke", "#334155")),
            "thickness": float(e.get_property("thickness", 1.0)),
            "glow": float(e.get_property("glow", 0.0)),
            "opacity": float(e.get_property("opacity", 1.0)),
            "points": e.get_property("points", []),
            "waypoints": e.get_property("waypoints", []),
            "tier": str(e.get_property("tier", "primary"))
        })

    connectors_data = []
    for c in scene.connectors:
        connectors_data.append({
            "name": c.name,
            "from": c.from_spec,
            "to": c.to_spec,
            "stroke": c.stroke,
            "thickness": c.thickness
        })

    return json.dumps({
        "success": True,
        "is_spatial": True,
        "name": scene.name,
        "background": scene.background,
        "entities": entities_data,
        "connectors": connectors_data,
        "day_cycle": scene.day_cycle_period
    })

def evaluate_frame_at(t: float) -> str:
    """Evaluates the active spatial scene at timestamp t."""
    from engine.runner import run_foxvc
    # Cached scene reference in global state
    global _ACTIVE_SCENE
    if '_ACTIVE_SCENE' not in globals() or not _ACTIVE_SCENE:
        return "{}"
    
    state = _ACTIVE_SCENE.evaluate_at(t)
    # Output: { name: [x, y, w, h, rot] }
    return json.dumps(state)

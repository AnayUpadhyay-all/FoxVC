"""
FoxVC Semantic Library System — End-to-End Execution Validator.
Tests Checkpoints 1 through 10 strictly using FoxVC source execution.
"""
import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from engine.runner import run_foxvc, run_foxvc_project
from engine.module_system import SemanticRegistry, SemanticModule, SemanticCapability

def assert_checkpoint(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}")
    if not condition:
        print(f"       ERROR DETAILS: {details}")
        sys.exit(1)

print("=" * 70)
print("FOXVC SEMANTIC LIBRARY SYSTEM: RUNTIME INTEGRATION TEST")
print("=" * 70)

# Checkpoint 1: Existing Regression Test Suite
import unittest
loader = unittest.TestLoader()
suite = loader.discover("tests")
runner = unittest.TextTestRunner(stream=open(os.devnull, "w"), verbosity=0)
res_unit = runner.run(suite)
assert_checkpoint(
    "1. Core Regression Test Suite Passes (85 tests)",
    res_unit.wasSuccessful() and res_unit.testsRun >= 85,
    f"Failures: {len(res_unit.failures)}, Errors: {len(res_unit.errors)}, Tests Run: {res_unit.testsRun}"
)

# Checkpoint 2: Single Library FoxVC Source Execution
res_single = run_foxvc_project(os.path.join(ROOT_DIR, "examples/test_single_lib.fox"))
assert_checkpoint("2. Single Library Load & Execute (.fox source)", res_single.success, res_single.error)
s0 = res_single.spatial_space.evaluate_at(0.0)
s1 = res_single.spatial_space.evaluate_at(1.0) # quarter period -> span/2 = 40.0
assert_checkpoint(
    "   -> Single Library Capability Semantic Effect (linear_track displacement)",
    abs(s1["Shuttle"][0] - 40.0) < 0.1 and abs(s0["Shuttle"][0]) < 0.1,
    f"Expected X=40.0 at t=1.0, got {s1['Shuttle'][0]}"
)

# Checkpoint 3: Dual Library FoxVC Source Execution
res_dual = run_foxvc_project(os.path.join(ROOT_DIR, "examples/test_dual_lib.fox"))
assert_checkpoint("3. Dual Library Composition (.fox source)", res_dual.success, res_dual.error)
sd0 = res_dual.spatial_space.evaluate_at(0.0)
sd1 = res_dual.spatial_space.evaluate_at(0.75) # quarter of 3s -> span/2 = 30.0
ent_sat = res_dual.spatial_space.entities["Satellite"]
assert_checkpoint(
    "   -> Dual Library Capabilities Composite Correctly (linear_track + beam_pulse)",
    abs(sd1["Satellite"][1] - 30.0) < 0.1 and ent_sat.get_property("thickness") > 1.0,
    f"Y displacement: {sd1['Satellite'][1]}, thickness: {ent_sat.get_property('thickness')}"
)

# Checkpoint 4: Namespace Collision & Deterministic Disambiguation
res_coll = run_foxvc_project(os.path.join(ROOT_DIR, "examples/test_namespace_collision.fox"))
assert_checkpoint("4. Namespace Collision Resolution (.fox source)", res_coll.success, res_coll.error)
sc_half = res_coll.spatial_space.evaluate_at(0.5) # quarter period
ang_rot = sc_half["AngularObject"][4]
scale_w = sc_half["ScaleObject"][2]
assert_checkpoint(
    "   -> spat.wobble modified rotation (30.0 deg), opt.wobble modified width (75.0)",
    abs(ang_rot - 30.0) < 0.1 and abs(scale_w - 75.0) < 0.1,
    f"Rotation: {ang_rot}, Width: {scale_w}"
)

# Checkpoint 5: Semantic Module Dependency DAG Resolution
dep_code = """
load "sensor.optics" as opt
space DepWorld
    entity Sensor
        form circle
        diameter 20
        apply Sensor opt.beam_pulse period 1.0
"""
res_dep = run_foxvc(dep_code)
assert_checkpoint(
    "5. Automatic Dependency Loading (sensor.optics pulls spatial.expansion)",
    res_dep.success,
    res_dep.error
)

# Checkpoint 6: Missing Dependency Detection & Clean Diagnostic
missing_dep_mod = SemanticModule("broken.module", "1.0.0", dependencies={"nonexistent.lib": "^1.0.0"})
SemanticRegistry.register(missing_dep_mod)
res_missing_dep = run_foxvc('load "broken.module"')
assert_checkpoint(
    "6. Missing Dependency Diagnostic Rejection",
    (not res_missing_dep.success) and ("Semantic module 'nonexistent.lib' not found" in res_missing_dep.error),
    res_missing_dep.error
)

# Checkpoint 7: SemVer Version Incompatibility Rejection
res_bad_ver = run_foxvc('load "spatial.expansion" version "^3.0.0"')
assert_checkpoint(
    "7. SemVer Version Incompatibility Diagnostic Rejection",
    (not res_bad_ver.success) and ("does not satisfy requested '^3.0.0'" in res_bad_ver.error),
    res_bad_ver.error
)

# Checkpoint 8: Missing Module Diagnostic Rejection
res_no_mod = run_foxvc('load "totally.unknown.library"')
assert_checkpoint(
    "8. Missing Module Diagnostic Rejection",
    (not res_no_mod.success) and ("Semantic module 'totally.unknown.library' not found" in res_no_mod.error),
    res_no_mod.error
)

# Checkpoint 9: Missing Capability Diagnostic Rejection
missing_cap_code = """
load "spatial.expansion"
space ErrSpace
    entity Box
        form rect size 20 by 20
        apply Box nonexistent_teleport distance 100
"""
res_missing_cap = run_foxvc(missing_cap_code)
assert_checkpoint(
    "9. Missing Capability Diagnostic Rejection",
    (not res_missing_cap.success) and ("Unknown visual rule or semantic capability 'nonexistent_teleport'" in res_missing_cap.error),
    res_missing_cap.error
)

# Checkpoint 10: Realistic Planetary Rover Workload Execution
res_rover = run_foxvc_project(os.path.join(ROOT_DIR, "examples/AutonomousRoverMission.fox"))
assert_checkpoint("10. Realistic Combined Planetary Rover Workload", res_rover.success, res_rover.error)
rover_scene = res_rover.spatial_space
assert_checkpoint(
    "    -> All Entities, Connectors, and Kinematic Hooks Resolved",
    len(rover_scene.entities) >= 5 and len(rover_scene.connectors) == 2,
    f"Entities: {len(rover_scene.entities)}, Connectors: {len(rover_scene.connectors)}"
)

print("=" * 70)
print("ALL 10 CHECKPOINTS VERIFIED: PASS")
print("=" * 70)

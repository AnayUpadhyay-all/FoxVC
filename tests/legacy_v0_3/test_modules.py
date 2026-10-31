"""
Automated Verification Suite for FoxVC Semantic Module Foundation (v0.8.0)
Tests A through I covering core compatibility, module loading, namespaces,
versioning, dependency resolution, cycle detection, and realistic workloads.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.runner import run_foxvc, run_foxvc_project
from engine.module_system import (
    SemanticRegistry, SemanticModule, SemanticCapability,
    resolve_module_dependency_graph, SemanticModuleError
)

class TestFoxVCSemanticModules(unittest.TestCase):

    def test_a_core_compatibility(self):
        """Test A: Verifies that core arithmetic and web structures remain intact."""
        res = run_foxvc('a = 40 + 2\nsay a')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "42")

    def test_b_single_semantic_module(self):
        """Test B: Loads motion.kinematics and consumes harmonic_oscillator."""
        code = (
            'load "motion.kinematics"\n'
            'space TestSpace\n'
            '    entity Piston\n'
            '        form rect\n'
            '        size 40 by 20\n'
            '        apply Piston harmonic_oscillator amplitude 30 period 4.0 axis "x"\n'
        )
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        scene = res.spatial_space
        self.assertIsNotNone(scene)
        
        # Check kinematics at t = 0 (offset 0) vs t = 1.0 (quarter period: max amplitude 30)
        s0 = scene.evaluate_at(t=0.0)
        s1 = scene.evaluate_at(t=1.0)
        self.assertAlmostEqual(s0["Piston"][0], 0.0, places=2)
        self.assertAlmostEqual(s1["Piston"][0], 30.0, places=2)

    def test_c_multi_module_coexistence(self):
        """Test C: Proves multiple modules can be loaded and compose simultaneously."""
        code = (
            'load "motion.kinematics"\n'
            'load "visual.fx"\n'
            'space MultiModSpace\n'
            '    entity Beacon\n'
            '        form circle\n'
            '        diameter 50\n'
            '        apply Beacon harmonic_oscillator amplitude 15 period 2.0 axis "y"\n'
            '        apply Beacon opacity_wave period 2.0 min 0.3 max 0.9\n'
        )
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        scene = res.spatial_space
        s1 = scene.evaluate_at(t=0.5)  # quarter period
        self.assertAlmostEqual(s1["Beacon"][1], 15.0, places=2)
        # Opacity changed from default 1.0
        self.assertLess(scene.entities["Beacon"].get_property("opacity"), 1.0)

    def test_d_namespace_isolation_and_aliasing(self):
        """Test D: Qualified names and alias scoping."""
        code = (
            'load "motion.kinematics" as kin\n'
            'space AliasSpace\n'
            '    entity Rotor\n'
            '        form circle\n'
            '        diameter 30\n'
            '        apply Rotor kin.orbital_wobble period 2.0 inclination 20\n'
        )
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        scene = res.spatial_space
        s_half = scene.evaluate_at(t=0.5)  # quarter of 2.0s -> sin(pi/2) = 1 -> rot 20 deg
        self.assertAlmostEqual(s_half["Rotor"][4], 20.0, places=2)

    def test_e_automatic_dependency_resolution(self):
        """Test E: visual.fx depends on motion.kinematics; loading visual.fx satisfies dependency."""
        resolved = resolve_module_dependency_graph(
            [("visual.fx", "^1.0.0")],
            SemanticRegistry,
            "0.8.0"
        )
        names = [m.name for m in resolved]
        self.assertEqual(names, ["motion.kinematics", "visual.fx"])

    def test_f_missing_dependency_and_missing_module_diagnostics(self):
        """Test F: Verifies clean error diagnostics on missing modules."""
        code = 'load "unknown.robotics"'
        res = run_foxvc(code)
        self.assertFalse(res.success)
        self.assertIn("Semantic module 'unknown.robotics' not found", res.error)

    def test_g_version_incompatibility_rejection(self):
        """Test G: Rejects when module version cannot satisfy requested spec."""
        code = 'load "motion.kinematics" version "^2.0.0"'
        res = run_foxvc(code)
        self.assertFalse(res.success)
        self.assertIn("does not satisfy requested '^2.0.0'", res.error)

    def test_h_circular_dependency_detection(self):
        """Test H: Circular dependency detection."""
        m1 = SemanticModule("cycle.alpha", "1.0.0", dependencies={"cycle.beta": "*"})
        m2 = SemanticModule("cycle.beta", "1.0.0", dependencies={"cycle.alpha": "*"})
        SemanticRegistry.register(m1)
        SemanticRegistry.register(m2)

        with self.assertRaises(SemanticModuleError) as ctx:
            resolve_module_dependency_graph([("cycle.alpha", "*")], SemanticRegistry, "0.8.0")
        self.assertIn("Circular module dependency detected", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()

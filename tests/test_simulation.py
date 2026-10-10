"""
FoxVC Simulation System & Expressive Boundary Tests
Tests realistic multi-tick state propagation and multi-variable dependencies.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.runner import run_foxvc, run_foxvc_diagnostic

class TestFoxVCSimulation(unittest.TestCase):

    def test_autonomous_simulation_workload_strict(self):
        with open("examples/simulation_system.fox", "r") as f:
            code = f.read()
        result = run_foxvc(code)
        self.assertTrue(result.success, f"Strict execution failed: {result.error}")
        self.assertIn("Overall Simulation Survival: true", result.output)

    def test_autonomous_simulation_workload_diagnostic(self):
        with open("examples/simulation_system.fox", "r") as f:
            code = f.read()
        res = run_foxvc_diagnostic(code)
        self.assertTrue(res.success)
        self.assertEqual(res.summary.failed, 0)
        self.assertEqual(res.summary.blocked, 0)
        self.assertGreater(res.summary.passed, 30)

if __name__ == "__main__":
    unittest.main()

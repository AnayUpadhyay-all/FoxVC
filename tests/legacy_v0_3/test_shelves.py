import unittest
from engine.runner import run_foxvc

class TestFoxVCShelfArchitecture(unittest.TestCase):
    def test_call_shelf(self):
        code = """call shelf "mathx"
say "called"
"""
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        self.assertIn("[Shelf Mounted: mathx]", res.output)
        self.assertIn("called", res.output)

    def test_shelf_declaration(self):
        code = """shelf "weave"
say "mounted"
"""
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        self.assertIn("[Shelf Mounted: weave]", res.output)
        self.assertIn("mounted", res.output)

    def test_shelf_load_item(self):
        code = """shelf "vortex" load "motion"
say "item_loaded"
"""
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        self.assertIn("[Shelf Item Loaded: vortex.motion]", res.output)
        self.assertIn("item_loaded", res.output)

    def test_auto_discovered_physics_shelf(self):
        code = """shelf "physics"
f = force(10, 9.8)
say "Force: " + f
"""
        res = run_foxvc(code)
        self.assertTrue(res.success, f"Failed: {res.error}")
        self.assertIn("Force: 98", res.output)

if __name__ == "__main__":
    unittest.main()

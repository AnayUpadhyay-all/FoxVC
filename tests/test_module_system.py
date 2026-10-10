import unittest
from engine.module_system import SemanticRegistry, SemanticModule, SemanticCapability, satisfies_semver, parse_semver
from engine.runner import run_foxvc

class TestSemanticModuleSystem(unittest.TestCase):
    def test_parse_semver(self):
        self.assertEqual(parse_semver("1.2.3"), (1, 2, 3))
        self.assertEqual(parse_semver("v2.0.0"), (2, 0, 0))
        self.assertEqual(parse_semver("3"), (3, 0, 0))

    def test_satisfies_caret(self):
        self.assertTrue(satisfies_semver("1.2.0", "^1.0.0"))
        self.assertTrue(satisfies_semver("1.0.0", "^1.0.0"))
        self.assertFalse(satisfies_semver("2.0.0", "^1.0.0"))
        self.assertFalse(satisfies_semver("0.9.0", "^1.0.0"))

    def test_satisfies_comparison_operators(self):
        self.assertTrue(satisfies_semver("2.0.0", ">=1.0.0"))
        self.assertTrue(satisfies_semver("1.5.0", "<=2.0.0"))
        self.assertTrue(satisfies_semver("2.1.0", ">2.0.0"))
        self.assertTrue(satisfies_semver("1.9.0", "<2.0.0"))
        self.assertTrue(satisfies_semver("1.2.3", "=1.2.3"))

    def test_registry_registration_and_retrieval(self):
        mod = SemanticModule("custom.tool", "1.0.0")
        SemanticRegistry.register(mod)
        retrieved = SemanticRegistry.get("custom.tool")
        self.assertEqual(retrieved.name, "custom.tool")

    def test_resolve_dependencies_single_module(self):
        resolved = SemanticRegistry.resolve_dependencies("spatial.expansion")
        self.assertTrue(any(m.name == "spatial.expansion" for m in resolved))

    def test_resolve_dependencies_dag_chain(self):
        resolved = SemanticRegistry.resolve_dependencies("sensor.optics")
        names = [m.name for m in resolved]
        self.assertIn("spatial.expansion", names)
        self.assertIn("sensor.optics", names)
        # spatial.expansion must precede sensor.optics
        self.assertLess(names.index("spatial.expansion"), names.index("sensor.optics"))

    def test_missing_module_error(self):
        res = run_foxvc('load "nonexistent.module"')
        self.assertFalse(res.success)
        self.assertIn("Semantic module 'nonexistent.module' not found", res.error)

    def test_missing_dependency_error(self):
        broken = SemanticModule("broken.mod", "1.0.0", dependencies={"missing.dep": "^1.0.0"})
        SemanticRegistry.register(broken)
        res = run_foxvc('load "broken.mod"')
        self.assertFalse(res.success)
        self.assertIn("Semantic module 'missing.dep' not found", res.error)

    def test_version_incompatibility_error(self):
        res = run_foxvc('load "spatial.expansion" version "^3.0.0"')
        self.assertFalse(res.success)
        self.assertIn("does not satisfy requested '^3.0.0'", res.error)

    def test_module_alias_loading(self):
        code = '''load "sensor.optics" as opt
say "Loaded alias"
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertIn("Loaded alias", res.output)

    def test_namespace_collision_resolution(self):
        code = '''load "spatial.expansion" as spat
load "sensor.optics" as opt
space TestSpace
    entity A
        form rect size 20 by 20
        apply A spat.wobble period 2.0 amplitude 30.0
    entity B
        form rect size 50 by 20
        apply B opt.wobble period 2.0 amplitude 25.0
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        sc = res.spatial_space.evaluate_at(0.5)
        self.assertAlmostEqual(sc["A"][4], 30.0, places=1)
        self.assertAlmostEqual(sc["B"][2], 75.0, places=1)

    def test_missing_capability_error(self):
        code = '''load "spatial.expansion"
space ErrSpace
    entity Box
        form rect size 20 by 20
        apply Box nonexistent_teleport distance 100
'''
        res = run_foxvc(code)
        self.assertFalse(res.success)
        self.assertIn("Unknown visual rule or semantic capability 'nonexistent_teleport'", res.error)

    def test_linear_track_capability_at_t0_and_quarter(self):
        code = '''load "spatial.expansion"
space Motion
    entity Shuttle
        form rect size 40 by 20
        apply Shuttle linear_track span 80 period 4.0
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        s0 = res.spatial_space.evaluate_at(0.0)
        s1 = res.spatial_space.evaluate_at(1.0)
        self.assertAlmostEqual(s0["Shuttle"][0], 0.0, places=1)
        self.assertAlmostEqual(s1["Shuttle"][0], 40.0, places=1)

    def test_beam_pulse_capability(self):
        code = '''load "sensor.optics"
space BeamSpace
    entity Sat
        form circle diameter 20
        apply Sat beam_pulse period 1.0
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        ent = res.spatial_space.entities["Sat"]
        self.assertGreater(ent.get_property("thickness"), 1.0)

    def test_circular_dependency_rejection(self):
        m1 = SemanticModule("circ.a", "1.0.0", dependencies={"circ.b": "^1.0.0"})
        m2 = SemanticModule("circ.b", "1.0.0", dependencies={"circ.a": "^1.0.0"})
        SemanticRegistry.register(m1)
        SemanticRegistry.register(m2)
        with self.assertRaises(ValueError) as ctx:
            SemanticRegistry.resolve_dependencies("circ.a")
        self.assertIn("Circular dependency", str(ctx.exception))

if __name__ == '__main__':
    unittest.main()

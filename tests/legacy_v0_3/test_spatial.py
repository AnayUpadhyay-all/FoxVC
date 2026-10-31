import unittest
from engine.spatial import SpatialSpace, SpatialEntity, SpatialConnector
from engine.runner import run_foxvc

class TestFoxVCSpatialEngine(unittest.TestCase):
    def test_create_space_and_add_entity(self):
        space = SpatialSpace("TestSpace")
        ent = SpatialEntity("Core", "circle", {"diameter": 40})
        space.add_entity(ent)
        self.assertIn("Core", space.entities)
        self.assertEqual(space.entities["Core"].form_kind, "circle")

    def test_entity_rect_dimensions(self):
        space = SpatialSpace("TestSpace")
        ent = SpatialEntity("Body", "rect", {"width": 80, "height": 40})
        space.add_entity(ent)
        coords = space.evaluate_at(0.0)
        self.assertEqual(coords["Body"][2], 80.0)
        self.assertEqual(coords["Body"][3], 40.0)

    def test_entity_circle_diameter_dimensions(self):
        space = SpatialSpace("TestSpace")
        ent = SpatialEntity("Wheel", "circle", {"diameter": 30})
        space.add_entity(ent)
        coords = space.evaluate_at(0.0)
        self.assertEqual(coords["Wheel"][2], 30.0)
        self.assertEqual(coords["Wheel"][3], 30.0)

    def test_entity_circle_radius_dimensions(self):
        space = SpatialSpace("TestSpace")
        ent = SpatialEntity("Hub", "circle", {"radius": 15})
        space.add_entity(ent)
        coords = space.evaluate_at(0.0)
        self.assertEqual(coords["Hub"][2], 30.0)
        self.assertEqual(coords["Hub"][3], 30.0)

    def test_beside_east_relation(self):
        space = SpatialSpace("S")
        c = SpatialEntity("Center", "rect", {"width": 40, "height": 40})
        e = SpatialEntity("Right", "rect", {"width": 20, "height": 20},
                          relations=[{"kind": "beside", "target": "Center", "params": {"direction": "east", "spacing": 10}}])
        space.add_entity(c)
        space.add_entity(e)
        coords = space.evaluate_at(0.0)
        # Center x=0, w=40; Right w=20, spacing=10 => x = 0 + 20 + 10 + 10 = 40.0
        self.assertAlmostEqual(coords["Right"][0], 40.0, places=1)

    def test_beside_west_relation(self):
        space = SpatialSpace("S")
        c = SpatialEntity("Center", "rect", {"width": 40, "height": 40})
        w = SpatialEntity("Left", "rect", {"width": 20, "height": 20},
                          relations=[{"kind": "beside", "target": "Center", "params": {"direction": "west", "spacing": 10}}])
        space.add_entity(c)
        space.add_entity(w)
        coords = space.evaluate_at(0.0)
        self.assertAlmostEqual(coords["Left"][0], -40.0, places=1)

    def test_beside_north_and_south_relations(self):
        space = SpatialSpace("S")
        c = SpatialEntity("Center", "rect", {"width": 40, "height": 40})
        n = SpatialEntity("Top", "rect", {"width": 20, "height": 20},
                          relations=[{"kind": "beside", "target": "Center", "params": {"direction": "north", "spacing": 5}}])
        s = SpatialEntity("Bottom", "rect", {"width": 20, "height": 20},
                          relations=[{"kind": "beside", "target": "Center", "params": {"direction": "south", "spacing": 5}}])
        space.add_entity(c)
        space.add_entity(n)
        space.add_entity(s)
        coords = space.evaluate_at(0.0)
        self.assertAlmostEqual(coords["Top"][1], -35.0, places=1)
        self.assertAlmostEqual(coords["Bottom"][1], 35.0, places=1)

    def test_inside_relation(self):
        space = SpatialSpace("S")
        parent = SpatialEntity("Chassis", "rect", {"width": 100, "height": 50})
        child = SpatialEntity("Core", "circle", {"diameter": 20},
                              relations=[{"kind": "inside", "target": "Chassis", "params": {}}])
        space.add_entity(parent)
        space.add_entity(child)
        coords = space.evaluate_at(0.0)
        self.assertEqual(coords["Core"][0], coords["Chassis"][0])
        self.assertEqual(coords["Core"][1], coords["Chassis"][1])

    def test_spin_behavior(self):
        space = SpatialSpace("S")
        ent = SpatialEntity("Spinner", "rect", {"width": 20, "height": 20},
                            behaviors=[{"kind": "spin", "params": {"period": 4.0}}])
        space.add_entity(ent)
        c0 = space.evaluate_at(0.0)
        c1 = space.evaluate_at(1.0) # quarter period -> 90 deg
        c2 = space.evaluate_at(2.0) # half period -> 180 deg
        self.assertAlmostEqual(c0["Spinner"][4], 0.0, places=1)
        self.assertAlmostEqual(c1["Spinner"][4], 90.0, places=1)
        self.assertAlmostEqual(c2["Spinner"][4], 180.0, places=1)

    def test_pulse_behavior(self):
        space = SpatialSpace("S")
        ent = SpatialEntity("Heart", "circle", {"diameter": 20},
                            behaviors=[{"kind": "pulse", "params": {"period": 2.0, "min": 0.5, "max": 1.5}}])
        space.add_entity(ent)
        c0 = space.evaluate_at(0.0) # sin(0) = 0 -> scale = 1.0 => diameter = 20.0
        c_half = space.evaluate_at(0.5) # quarter period -> scale = 1.5 => diameter = 30.0
        self.assertAlmostEqual(c0["Heart"][2], 20.0, places=1)
        self.assertAlmostEqual(c_half["Heart"][2], 30.0, places=1)

    def test_add_connector(self):
        space = SpatialSpace("S")
        conn = SpatialConnector("Link1", "NodeA", "NodeB", {"stroke": "#ff0000", "thickness": 2})
        space.add_connector(conn)
        self.assertIn("Link1", space.connectors)
        self.assertEqual(space.connectors["Link1"].from_spec, "NodeA")

    def test_space_script_execution(self):
        code = '''space Dashboard
    entity Engine form circle diameter 50
    entity Status form rect size 40 by 20
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertEqual(len(res.spatial_space.entities), 2)
        self.assertIn("Engine", res.spatial_space.entities)
        self.assertIn("Status", res.spatial_space.entities)

    def test_replicate_creates_multiple_entities(self):
        code = '''space ParticleWorld
    replicate 5 of entity Dot
        form circle diameter 4
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertEqual(len(res.spatial_space.entities), 5)
        self.assertIn("Dot_1", res.spatial_space.entities)
        self.assertIn("Dot_5", res.spatial_space.entities)

    def test_connector_script_execution(self):
        code = '''space Circuit
    entity PinA form circle diameter 10
    entity PinB form circle diameter 10
    connect Wire from PinA to PinB
        stroke "#00ff00"
        thickness 3.0
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertEqual(len(res.spatial_space.connectors), 1)
        self.assertIn("Wire", res.spatial_space.connectors)

    def test_get_and_set_entity_property(self):
        ent = SpatialEntity("Sensor", "rect", {"sensitivity": 95})
        self.assertEqual(ent.get_property("sensitivity"), 95)
        ent.set_property("sensitivity", 99)
        self.assertEqual(ent.get_property("sensitivity"), 99)

if __name__ == '__main__':
    unittest.main()

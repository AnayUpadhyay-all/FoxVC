"""
Automated Tests for FoxVC Advanced 2D World Engine (v0.7.0)
Validates autonomous living worlds, camera tracking, piecewise path travel,
state machine progression, and hierarchical environmental containment.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.spatial import SpatialEntity, SpatialRelation, SpatialScene, CameraModel
from engine.runner import run_foxvc, run_foxvc_project

class TestFoxVCLivingWorld(unittest.TestCase):

    def test_piecewise_path_interpolation(self):
        scene = SpatialScene("TransitWorld")
        road = SpatialEntity("Road", "path")
        road.set_property("waypoints", [0.0, 0.0, 100.0, 0.0, 100.0, 100.0])

        car = SpatialEntity("Car", "rect")
        car.relations.append(SpatialRelation("travels", "Road", period=10.0))

        scene.add_entity(road)
        scene.add_entity(car)
        scene.resolve()

        # At t = 0.0 -> Start point: (0, 0)
        s0 = scene.evaluate_at(t=0.0)
        self.assertAlmostEqual(s0["Car"][0], 0.0, places=2)
        self.assertAlmostEqual(s0["Car"][1], 0.0, places=2)

        # At t = 2.5 (quarter period) -> halfway down first segment: (50, 0)
        s25 = scene.evaluate_at(t=2.5)
        self.assertAlmostEqual(s25["Car"][0], 50.0, places=2)
        self.assertAlmostEqual(s25["Car"][1], 0.0, places=2)

        # At t = 5.0 (half period) -> corner waypoint: (100, 0)
        s5 = scene.evaluate_at(t=5.0)
        self.assertAlmostEqual(s5["Car"][0], 100.0, places=2)
        self.assertAlmostEqual(s5["Car"][1], 0.0, places=2)

        # At t = 7.5 -> halfway down second segment: (100, 50)
        s75 = scene.evaluate_at(t=7.5)
        self.assertAlmostEqual(s75["Car"][0], 100.0, places=2)
        self.assertAlmostEqual(s75["Car"][1], 50.0, places=2)

    def test_nested_containment_propagation(self):
        """Moving the town automatically propagates coordinates to house, room, and table."""
        scene = SpatialScene("HierarchyWorld")
        town = SpatialEntity("Town", "rect")
        town.resolved_x = 200.0
        town.resolved_y = 150.0

        house = SpatialEntity("House", "rect")
        house.relations.append(SpatialRelation("inside", "Town", offset_x=50.0, offset_y=20.0))

        room = SpatialEntity("Room", "rect")
        room.relations.append(SpatialRelation("inside", "House", offset_x=10.0, offset_y=5.0))

        table = SpatialEntity("Table", "rect")
        table.relations.append(SpatialRelation("inside", "Room", offset_x=4.0, offset_y=2.0))

        scene.add_entity(town)
        scene.add_entity(house)
        scene.add_entity(room)
        scene.add_entity(table)
        scene.resolve()

        st = scene.evaluate_at(0.0)
        # Expected Table X: 200 + 50 + 10 + 4 = 264
        # Expected Table Y: 150 + 20 + 5 + 2 = 177
        self.assertEqual(st["Table"][0], 264.0)
        self.assertEqual(st["Table"][1], 177.0)

    def test_semantic_camera_tracking(self):
        scene = SpatialScene("CamWorld")
        target = SpatialEntity("Hero", "circle")
        target.resolved_x = 420.0
        target.resolved_y = -310.0

        scene.add_entity(target)
        scene.camera.mode = "follows"
        scene.camera.target = "Hero"
        scene.resolve()

        st = scene.evaluate_at(0.0)
        self.assertEqual(st["Hero"][0], 420.0)
        self.assertEqual(st["Hero"][1], -310.0)
        self.assertEqual(scene.camera.target, "Hero")

    def test_living_world_workload_execution(self):
        path = os.path.abspath("examples/LivingWorld.fox")
        res = run_foxvc_project(path)
        self.assertTrue(res.success, f"Failed: {res.error}")
        self.assertIsNotNone(res.spatial_space)
        self.assertEqual(res.spatial_space.camera.target, "AutonomousTransitCar")
        self.assertGreater(len(res.spatial_space.entities), 20)

if __name__ == "__main__":
    unittest.main()

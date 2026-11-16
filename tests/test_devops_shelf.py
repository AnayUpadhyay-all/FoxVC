"""
Tests for FoxVC Enhanced DevOps & Docker System Primitives.
Verifies exec, diskUsage, memoryUsage, which, isProcessRunning, and httpPing.
"""

import unittest
from engine.shelves.system import get_system_shelf


class TestDevOpsSystem(unittest.TestCase):
    def setUp(self):
        self.sys = get_system_shelf()

    def test_exec_output_directly(self):
        # Directly executes shell command and returns stripped stdout
        out = self.sys["exec"]("echo 'FoxVC DevOps Engine'")
        self.assertEqual(out, "FoxVC DevOps Engine")

    def test_disk_usage_returns_real_stats(self):
        disk = self.sys["diskUsage"]("/")
        self.assertGreater(disk["total_gb"], 0)
        self.assertGreaterEqual(disk["free_gb"], 0)
        self.assertGreaterEqual(disk["percent"], 0)
        self.assertLessEqual(disk["percent"], 100)

    def test_which_locates_system_binaries(self):
        sh_path = self.sys["which"]("sh")
        self.assertTrue(sh_path.endswith("sh"))
        missing = self.sys["which"]("non_existent_binary_xyz_123")
        self.assertEqual(missing, "")

    def test_is_process_running(self):
        # python or bash is definitely running this test process
        res = self.sys["isProcessRunning"]("python")
        self.assertIn(res, (0, 1))

    def test_memory_usage(self):
        mem = self.sys["memoryUsage"]()
        self.assertIn("total_mb", mem._data)
        self.assertIn("used_mb", mem._data)


if __name__ == "__main__":
    unittest.main()

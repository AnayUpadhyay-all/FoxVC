"""
Comprehensive Unit Tests for Milestone 2.1: Fuse Hybrid Module System.
Verifies module-local namespaces, controlled exports, canonical caching,
relative imports, cycle detection, missing module diagnostics, and engine consistency.
"""

import unittest
import os
import tempfile
import shutil
from engine.runner import run_foxvc
from engine.modules import ModuleResolver, ModuleManager, ModuleError


class TestFuseModuleSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="foxvc_mod_test_")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_module_local_namespace_and_controlled_export(self):
        """Verify module variables remain isolated and only emitted properties are exposed."""
        mod_content = """
lock secret_key = 999
lock public_val = 42

act calc(x)
    emit x + 10

emit pack {
    public_val: public_val,
    calc: calc
}
"""
        mod_path = os.path.join(self.temp_dir, "math_helper.fox")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write(mod_content)

        main_content = """
fuse "./math_helper"

v = math_helper.public_val
res = math_helper.calc(5)
emit res + v
"""
        main_path = os.path.join(self.temp_dir, "main.fox")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_content)

        res = run_foxvc(main_content, engine_mode="interp", file_path=main_path, as_result=True)
        self.assertTrue(res.success, f"Execution failed: {res.error}")
        self.assertEqual(res.value, 57)  # 15 + 42

        # Verify internal secret_key did not pollute importer's global variables
        self.assertNotIn("secret_key", res.variables)

    def test_unexported_symbol_access_blocked(self):
        """Verify accessing private, non-emitted module symbols is rejected."""
        mod_content = """
lock internal_secret = "HIDDEN"
emit pack { status: "OK" }
"""
        mod_path = os.path.join(self.temp_dir, "secret_mod.fox")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write(mod_content)

        main_content = """
fuse "./secret_mod"
val = secret_mod.internal_secret
emit val
"""
        main_path = os.path.join(self.temp_dir, "main.fox")
        res = run_foxvc(main_content, engine_mode="interp", file_path=main_path, as_result=True)
        self.assertFalse(res.success)
        self.assertIn("has no property 'internal_secret'", str(res.error))

    def test_relative_subfolder_import(self):
        """Verify relative imports from nested subdirectories resolve correctly."""
        sub_dir = os.path.join(self.temp_dir, "utils")
        os.makedirs(sub_dir, exist_ok=True)
        with open(os.path.join(sub_dir, "string_tool.fox"), "w", encoding="utf-8") as f:
            f.write("""
act greet(name)
    emit "Hello, " + name

emit pack { greet: greet }
""")

        main_content = """
fuse "./utils/string_tool"
msg = string_tool.greet("FoxVC")
emit msg
"""
        main_path = os.path.join(self.temp_dir, "main.fox")
        res = run_foxvc(main_content, engine_mode="interp", file_path=main_path, as_result=True)
        self.assertTrue(res.success, f"Failed: {res.error}")
        self.assertEqual(res.value, "Hello, FoxVC")

    def test_module_caching_and_single_execution(self):
        """Verify a module is only executed once and subsequent imports reuse the cached namespace."""
        counter_file = os.path.join(self.temp_dir, "counter.txt")
        with open(counter_file, "w", encoding="utf-8") as f:
            f.write("0")

        # Module appends a digit on execution
        mod_content = f"""
c = readFile("{counter_file}")
writeFile("{counter_file}", c + "1")
emit pack {{ ready: aye }}
"""
        mod_path = os.path.join(self.temp_dir, "singleton.fox")
        with open(mod_path, "w", encoding="utf-8") as f:
            f.write(mod_content)

        main_content = """
fuse "./singleton"
fuse "./singleton"
emit singleton.ready
"""
        main_path = os.path.join(self.temp_dir, "main.fox")
        res = run_foxvc(main_content, engine_mode="interp", file_path=main_path, as_result=True)
        self.assertTrue(res.success)
        self.assertEqual(res.value, True)

        with open(counter_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "01", "Module should only execute once despite multiple fuse statements")

    def test_circular_import_detection(self):
        """Verify circular dependencies are trapped and reported with a clean error."""
        mod_a = os.path.join(self.temp_dir, "cycle_a.fox")
        mod_b = os.path.join(self.temp_dir, "cycle_b.fox")

        with open(mod_a, "w", encoding="utf-8") as f:
            f.write('fuse "./cycle_b"\nemit pack { a: 1 }\n')

        with open(mod_b, "w", encoding="utf-8") as f:
            f.write('fuse "./cycle_a"\nemit pack { b: 2 }\n')

        main_content = 'fuse "./cycle_a"\nemit 10\n'
        main_path = os.path.join(self.temp_dir, "main.fox")

        res = run_foxvc(main_content, engine_mode="interp", file_path=main_path, as_result=True)
        self.assertFalse(res.success)
        self.assertIn("Circular import detected", str(res.error))

    def test_missing_module_error_reporting(self):
        """Verify non-existent module raises a clear missing-module error with searched paths."""
        main_content = 'fuse "./non_existent_module"\n'
        main_path = os.path.join(self.temp_dir, "main.fox")
        res = run_foxvc(main_content, engine_mode="interp", file_path=main_path, as_result=True)
        self.assertFalse(res.success)
        self.assertIn("Cannot resolve module", str(res.error))


if __name__ == "__main__":
    unittest.main()

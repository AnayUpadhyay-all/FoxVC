import os
import sys
import tempfile
import unittest
import subprocess

from engine.builder import StandaloneCompiler, BuildResult, BuildError, build_standalone_binary


class TestStandaloneCompiler(unittest.TestCase):
    def setUp(self):
        self.compiler = StandaloneCompiler()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_find_c_compiler(self):
        compiler_info = StandaloneCompiler.find_c_compiler()
        self.assertIsNotNone(compiler_info, "C compiler (gcc/clang/cl) should be found on system")
        compiler_path, compiler_type = compiler_info
        self.assertTrue(os.path.exists(compiler_path))
        self.assertIn(compiler_type, ("gcc", "clang", "cl"))

    def test_generate_c_source(self):
        fox_file = os.path.join(self.temp_dir.name, "simple.fox")
        with open(fox_file, "w") as f:
            f.write("say \"Standalone FoxVC!\"\n")

        c_file = os.path.join(self.temp_dir.name, "simple.c")
        result = self.compiler.build(fox_file, output_path=c_file, emit_c=True)

        self.assertTrue(result.success)
        self.assertEqual(result.target, "c_source")
        self.assertTrue(os.path.exists(c_file))

        with open(c_file, "r") as f:
            content = f.read()

        self.assertIn("FOX_EMBEDDED_BYTECODE", content)
        self.assertIn("FOX_EMBEDDED_STR_CONSTS", content)
        self.assertIn("Standalone FoxVC!", content)
        self.assertIn("int main(int argc, char** argv)", content)

    def test_build_and_run_hello(self):
        fox_file = os.path.join(self.temp_dir.name, "hello.fox")
        with open(fox_file, "w") as f:
            f.write("say \"Hello from Standalone Binary!\"\n")

        bin_file = os.path.join(self.temp_dir.name, "hello_bin")
        result = self.compiler.build(fox_file, output_path=bin_file)

        self.assertTrue(result.success)
        self.assertEqual(result.target, "c_binary")
        self.assertTrue(os.path.exists(bin_file))
        self.assertGreater(result.binary_size_bytes, 1000)

        # Execute the standalone binary directly
        proc = subprocess.run([bin_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Hello from Standalone Binary!", proc.stdout)

    def test_build_and_run_math_and_acts(self):
        fox_file = os.path.join(self.temp_dir.name, "calc.fox")
        with open(fox_file, "w") as f:
            f.write("""
act compute(a, b)
    lock acc = a
    lock count = 0
    spin count < b
        acc = acc + 2
        count = count + 1
    emit acc

lock answer = compute(10, 5)
say answer
""")

        bin_file = os.path.join(self.temp_dir.name, "calc_bin")
        result = self.compiler.build(fox_file, output_path=bin_file)

        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(bin_file))

        # Execute binary directly: compute(10, 5) should produce 10 + 5*2 = 20
        proc = subprocess.run([bin_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("20", proc.stdout.strip().splitlines())

    def test_build_standalone_binary_helper(self):
        fox_file = os.path.join(self.temp_dir.name, "helper.fox")
        with open(fox_file, "w") as f:
            f.write("lock x = 42\nsay x\n")

        bin_file = os.path.join(self.temp_dir.name, "helper_bin")
        out_path = build_standalone_binary(fox_file, bin_file)

        self.assertEqual(out_path, os.path.abspath(bin_file))
        self.assertTrue(os.path.exists(bin_file))

        proc = subprocess.run([bin_file], stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "42")

    def test_emit_llvm_ir(self):
        fox_file = os.path.join(self.temp_dir.name, "llvm_test.fox")
        with open(fox_file, "w") as f:
            f.write("say \"LLVM from FoxVC\"\n")

        ll_file = os.path.join(self.temp_dir.name, "llvm_test.ll")
        result = self.compiler.build(fox_file, output_path=ll_file, emit_llvm=True)

        self.assertTrue(result.success)
        self.assertTrue(os.path.exists(ll_file))
        with open(ll_file, "r") as f:
            ll_content = f.read()
        self.assertIn("target triple", ll_content)
        self.assertIn("FOX_EMBEDDED_BYTECODE", ll_content)

    def test_target_resolution(self):
        self.assertEqual(self.compiler.resolve_target("windows"), ("x86_64-w64-mingw32", ".exe"))
        self.assertEqual(self.compiler.resolve_target("macos"), ("aarch64-apple-darwin", ""))
        self.assertEqual(self.compiler.resolve_target("wasm"), ("wasm32-unknown-wasi", ".wasm"))
        self.assertEqual(self.compiler.resolve_target("linux-arm64"), ("aarch64-unknown-linux-gnu", ""))

    def test_build_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            self.compiler.build("/tmp/this_file_should_not_exist_xyz.fox")


if __name__ == "__main__":
    unittest.main()

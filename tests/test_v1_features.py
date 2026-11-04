"""
Comprehensive Unit Test Suite for FoxVC v1.0 Features:
1. Canonical Formatter (foxvc fmt)
2. Static Analysis Linter (foxvc lint)
3. Native Automated Test Runner (foxvc test)
4. Language Server Protocol (foxvc lsp)
5. CVM 2.0 Native Struct/Member VM execution
6. Standard Library Shelves: data, audio, socket
"""

import unittest
import os
import tempfile

from engine.formatter import FoxFormatter
from engine.linter import FoxLinter
from engine.tester import FoxTestRunner
from engine.lsp import FoxLanguageServer
from engine.c_vm import FoxCVM
from engine.bytecode import Op
from engine.runner import run_foxvc
from engine.shelves.data import get_data_shelf
from engine.shelves.audio import get_audio_shelf
from engine.shelves.socket import get_socket_shelf


class TestFoxVCV1Features(unittest.TestCase):

    def setUp(self):
        self.formatter = FoxFormatter()
        self.linter = FoxLinter()
        self.runner = FoxTestRunner()
        self.lsp = FoxLanguageServer()

    # --- 1. Formatter Tests ---
    def test_formatter_normalizes_spacing_and_preserves_strings(self):
        raw = 'lock   x=10+5\nsay   "Hello == World + 10"'
        formatted = self.formatter.format_source(raw)
        self.assertIn('lock x = 10 + 5', formatted)
        # Strings must be preserved exactly without operator mangling
        self.assertIn('"Hello == World + 10"', formatted)

    def test_formatter_indentation_alignment(self):
        raw = "act calculate()\n  lock sum = 1 + 2\n  emit sum\n"
        formatted = self.formatter.format_source(raw)
        lines = formatted.strip().splitlines()
        self.assertEqual(lines[0], "act calculate()")
        self.assertTrue(lines[1].startswith("    lock sum = 1 + 2"))

    # --- 2. Linter Tests ---
    def test_linter_detects_unmutated_shift(self):
        code = "shift unmutated_var = 100\nsay unmutated_var\n"
        msgs = self.linter.lint_source(code)
        codes = [m.code for m in msgs]
        self.assertIn("W001", codes)  # Suggest lock

    def test_linter_detects_unused_variable(self):
        code = "lock never_used = 42\nsay 10\n"
        msgs = self.linter.lint_source(code)
        codes = [m.code for m in msgs]
        self.assertIn("W002", codes)

    def test_linter_detects_illegal_lock_mutation(self):
        code = "lock const_val = 10\nconst_val = 20\n"
        msgs = self.linter.lint_source(code)
        codes = [m.code for m in msgs]
        self.assertIn("E003", codes)

    # --- 3. Native Test Runner Tests ---
    def test_runner_executes_suite(self):
        code = (
            "act test_add()\n"
            "    lock a = 5\n"
            "    lock b = 10\n"
            "    guard a + b == 15\n"
            "    emit aye\n"
        )
        with tempfile.NamedTemporaryFile(suffix=".fox", mode="w", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            results = self.runner.run_file_suite(tmp_path)
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].passed)
            self.assertEqual(results[0].test_name, "test_add")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # --- 4. Language Server Protocol Tests ---
    def test_lsp_completion_and_hover(self):
        init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = self.lsp.handle_request(init_req)
        self.assertTrue(resp["result"]["capabilities"]["hoverProvider"])

        comp_req = {"jsonrpc": "2.0", "id": 2, "method": "textDocument/completion", "params": {}}
        c_resp = self.lsp.handle_request(comp_req)
        labels = [item["label"] for item in c_resp["result"]]
        self.assertIn("lock", labels)
        self.assertIn("fuse", labels)
        self.assertIn("data", labels)

    # --- 5. CVM 2.0 Native Object/Struct Member Execution ---
    def test_cvm2_native_guard_and_member_access(self):
        cvm = FoxCVM()
        # [BUILD_PACK reg 1 with field 'age'=25], [GET_MEMBER reg 2 from obj reg 1 'age'], [RETURN reg 2]
        instructions = [
            (Op.LOAD_CONST, 0, 25.0),
            (Op.BUILD_PACK, 1, [("age", 0)]),
            (Op.GET_MEMBER, 2, 1, "age"),
            (Op.GUARD, 2),
            (Op.RETURN, 2),
            (Op.HALT,)
        ]
        flat, nums, strs = cvm.compile_payload((instructions, {}))
        res = cvm.run_flat(flat, nums, strs)
        self.assertEqual(res, 25.0)

    # --- 6. Standard Shelves: Data, Audio, Socket ---
    def test_data_shelf(self):
        data = get_data_shelf()
        json_out = data["jsonStringify"]({"name": "FoxVC", "speed": 100})
        self.assertIn('"speed": 100', json_out)
        parsed = data["jsonParse"](json_out)
        self.assertEqual(parsed.get("name"), "FoxVC")

        b64 = data["b64Encode"]("Hello CVM")
        self.assertEqual(data["b64Decode"](b64), "Hello CVM")

    def test_audio_shelf_synthesis(self):
        audio = get_audio_shelf()
        samples = audio["synthSine"](440, 0.05, 0.2, 8000)
        self.assertEqual(len(samples), 400)
        self.assertTrue(all(-1.0 <= s <= 1.0 for s in samples))

    def test_socket_shelf_ws_framing(self):
        sock = get_socket_shelf()
        hex_frame = sock["wsFrameEncode"]("Ping Test")
        decoded = sock["wsFrameDecode"](hex_frame)
        self.assertEqual(decoded, "Ping Test")

    def test_end_to_end_fuse_data_runtime(self):
        script = (
            "fuse data\n"
            "lock raw = '{\"engine\": \"foxvm\", \"version\": 1.0}'\n"
            "lock parsed = data.jsonParse(raw)\n"
            "say 'Loaded Engine: ' + parsed.engine\n"
        )
        res = run_foxvc(script)
        self.assertTrue(res.success)
        self.assertIn("Loaded Engine: foxvm", res.output)


if __name__ == "__main__":
    unittest.main()

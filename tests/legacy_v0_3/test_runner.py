import unittest
import os
from engine.runner import (
    run_foxvc, run_foxvc_project, run_foxvc_diagnostic,
    detect_source_format, _sanitize_result
)
from engine.runtime import SourceFormat, ExecutionResult, DiagnosticCategory

class TestFoxVCRunner(unittest.TestCase):
    def test_run_foxvc_clean_execution(self):
        res = run_foxvc('say "Test OK"')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "Test OK")
        self.assertEqual(len(res.diagnostics), 0)

    def test_run_foxvc_empty_source(self):
        res = run_foxvc("")
        self.assertTrue(res.success)
        self.assertEqual(res.output, "")

    def test_run_foxvc_none_source(self):
        res = run_foxvc(None)
        self.assertTrue(res.success)
        self.assertEqual(res.output, "")

    def test_run_foxvc_syntax_error_handling(self):
        res = run_foxvc('say "unterminated')
        self.assertFalse(res.success)
        self.assertTrue(len(res.diagnostics) > 0)
        self.assertIn("Unterminated string", res.error)

    def test_run_foxvc_runtime_error_handling(self):
        res = run_foxvc('x = 10 / 0')
        self.assertFalse(res.success)
        self.assertIn("Division by zero", res.error)

    def test_run_foxvc_project_valid_file(self):
        res = run_foxvc_project("main.fox")
        self.assertTrue(res.success, res.error)
        self.assertIn("Speed: 15", res.output)

    def test_run_foxvc_project_directory(self):
        res = run_foxvc_project(".")
        self.assertTrue(res.success, res.error)

    def test_run_foxvc_project_nonexistent(self):
        res = run_foxvc_project("nonexistent_path_9999.fox")
        self.assertFalse(res.success)
        self.assertIn("not found", res.error)

    def test_run_foxvc_project_none(self):
        res = run_foxvc_project(None)
        self.assertFalse(res.success)

    def test_run_foxvc_diagnostic_clean(self):
        diags = run_foxvc_diagnostic('say "all good"')
        self.assertEqual(len(diags), 0)

    def test_run_foxvc_diagnostic_syntax_error(self):
        diags = run_foxvc_diagnostic('say "broken')
        self.assertGreater(len(diags), 0)
        self.assertEqual(diags[0].category, DiagnosticCategory.ERROR)

    def test_run_foxvc_diagnostic_empty(self):
        diags = run_foxvc_diagnostic("")
        self.assertEqual(len(diags), 1)
        self.assertEqual(diags[0].category, DiagnosticCategory.WARNING)

    def test_detect_source_format(self):
        self.assertEqual(detect_source_format("main.fox"), SourceFormat.FOXVC)
        self.assertEqual(detect_source_format("design.fskin"), SourceFormat.SKIN)
        self.assertEqual(detect_source_format("main.fweb"), SourceFormat.WEB)
        self.assertEqual(detect_source_format("app.flogic"), SourceFormat.LOGIC)
        self.assertEqual(detect_source_format("project.json"), SourceFormat.PROJECT)
        self.assertEqual(detect_source_format(None), SourceFormat.UNKNOWN)

    def test_execution_result_bool_evaluation(self):
        res_ok = ExecutionResult(success=True)
        res_err = ExecutionResult(success=False)
        self.assertTrue(bool(res_ok))
        self.assertFalse(bool(res_err))

    def test_sanitize_result_fallback(self):
        res = _sanitize_result(None)
        self.assertFalse(res.success)
        self.assertIsNotNone(res.spatial_object)

if __name__ == '__main__':
    unittest.main()

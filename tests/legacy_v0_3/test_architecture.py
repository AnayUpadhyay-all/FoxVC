"""
FoxVC Architectural Boundary & Diagnostic Execution Tests
Verifies zero GUI imports in engine, decoupled runtime contracts,
and PASS / FAIL / BLOCKED diagnostic execution with dependency tracking.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.runner import run_foxvc, run_foxvc_diagnostic
from engine.runtime import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StatementStatus,
    FOXVC_LANGUAGE_VERSION,
    FOXVC_RUNTIME_VERSION
)

class TestFoxVCArchitecture(unittest.TestCase):

    def test_engine_has_zero_gui_imports(self):
        """Verify that engine modules never import tkinter or UI code."""
        engine_modules = [
            "engine.lexer",
            "engine.parser",
            "engine.interpreter",
            "engine.runner",
            "engine.runtime"
        ]
        for mod_name in engine_modules:
            __import__(mod_name)
            mod = sys.modules[mod_name]
            for attr, val in mod.__dict__.items():
                self.assertNotIn("tkinter", str(val).lower(), f"Forbidden GUI import found in {mod_name}: {attr}")

    def test_runtime_contract_structured_diagnostics(self):
        """Verify structured diagnostics format correctly on runtime error."""
        code = 'x = 10 / 0'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertEqual(len(result.diagnostics), 1)
        diag = result.diagnostics[0]
        self.assertEqual(diag.category, DiagnosticCategory.MATH)
        self.assertEqual(diag.severity, DiagnosticSeverity.ERROR)
        self.assertEqual(diag.line, 1)
        self.assertIn("Division by zero", diag.message)

    def test_runtime_contract_version_metadata(self):
        """Verify execution result contains decoupled version metadata."""
        result = run_foxvc('say "Architecture Test"')
        self.assertTrue(result.success)
        self.assertEqual(result.metadata["language_version"], FOXVC_LANGUAGE_VERSION)
        self.assertEqual(result.metadata["runtime_version"], FOXVC_RUNTIME_VERSION)
        self.assertEqual(result.metadata["statement_count"], 1)

    def test_headless_input_sink_decoupling(self):
        """Verify that input_sink functions purely through abstract callable protocols."""
        inputs = ["FoxPilot"]
        result = run_foxvc('name = ask "ID: "\nsay "Welcome " + name', input_source=lambda prompt: inputs.pop())
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Welcome FoxPilot")

    # Diagnostic Execution Tests (PASS, FAIL, BLOCKED)
    def test_diagnostic_execution_pass_fail_blocked_flow(self):
        code = (
            "a = 10\n"
            "b = unknown_var\n"
            "c = b + 5\n"
            "d = 100 * 2\n"
            "e = d + 50\n"
        )
        res = run_foxvc_diagnostic(code)
        self.assertFalse(res.success)
        reports = res.statement_reports
        self.assertEqual(len(reports), 5)

        # a -> PASS
        self.assertEqual(reports[0].status, StatementStatus.PASS)
        self.assertEqual(reports[0].variable, "a")
        self.assertEqual(reports[0].value, "10")

        # b -> FAIL (unknown_var is undefined)
        self.assertEqual(reports[1].status, StatementStatus.FAIL)
        self.assertEqual(reports[1].variable, "b")
        self.assertIn("Unknown name: 'unknown_var'", reports[1].diagnostic.message)

        # c -> BLOCKED (depends on failed variable 'b')
        self.assertEqual(reports[2].status, StatementStatus.BLOCKED)
        self.assertEqual(reports[2].variable, "c")
        self.assertIn("depends on failed variable 'b'", reports[2].blocked_reason)

        # d -> PASS (independent continuation)
        self.assertEqual(reports[3].status, StatementStatus.PASS)
        self.assertEqual(reports[3].variable, "d")
        self.assertEqual(reports[3].value, "200")

        # e -> PASS (depends on healthy 'd')
        self.assertEqual(reports[4].status, StatementStatus.PASS)
        self.assertEqual(reports[4].variable, "e")
        self.assertEqual(reports[4].value, "250")

        # Summary check
        self.assertEqual(res.summary.passed, 3)
        self.assertEqual(res.summary.failed, 1)
        self.assertEqual(res.summary.blocked, 1)

    def test_diagnostic_execution_syntax_error_recovery(self):
        code = (
            "good = 10\n"
            "bad = 10 + \n"
            "other = 50 * 2\n"
        )
        res = run_foxvc_diagnostic(code)
        self.assertFalse(res.success)
        reports = res.statement_reports
        self.assertEqual(reports[0].status, StatementStatus.PASS)
        self.assertEqual(reports[1].status, StatementStatus.FAIL)
        self.assertEqual(reports[2].status, StatementStatus.PASS)
        self.assertEqual(res.summary.passed, 2)
        self.assertEqual(res.summary.failed, 1)

if __name__ == "__main__":
    unittest.main()

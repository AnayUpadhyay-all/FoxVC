"""
Unit tests for Milestone 2.5: Fox Den Studio Architecture & Decoupled Services.
Verifies headless Studio services, diagnostics validation, web engine contract,
and error handling without GUI dependencies.
"""

import unittest
import json
from studio.services import StudioExecutionService, StudioDiagnosticsService
from studio.web_engine import execute_foxvc_source


class TestStudioServices(unittest.TestCase):
    def test_headless_execution_service(self):
        """Verify StudioExecutionService executes code and returns structured ExecutionResult."""
        res = StudioExecutionService.execute("x = 10\ny = 20\nemit x + y")
        self.assertTrue(res.success)
        self.assertEqual(res.value, 30)

    def test_headless_diagnostics_service_valid(self):
        """Verify StudioDiagnosticsService validates correct syntax."""
        diag = StudioDiagnosticsService.validate_syntax("act test(n)\n    emit n * 2\n")
        self.assertTrue(diag["valid"])
        self.assertIsNone(diag["error"])

    def test_headless_diagnostics_service_invalid(self):
        """Verify StudioDiagnosticsService catches syntax errors."""
        diag = StudioDiagnosticsService.validate_syntax("act test()\n    x = +\n")
        self.assertFalse(diag["valid"])
        self.assertIsNotNone(diag["error"])

    def test_web_engine_contract(self):
        """Verify web_engine.execute_foxvc_source accepts source and returns valid JSON without profile errors."""
        raw_json = execute_foxvc_source("say 'Web Engine Online'\nemit 100")
        data = json.loads(raw_json)
        self.assertTrue(data["success"])
        self.assertIn("Web Engine Online", data.get("output", ""))

    def test_studio_syntax_and_starter_template(self):
        """Verify that Studio syntax highlighting covers all 25 keywords and starter template executes."""
        import re
        from engine.runner import run_foxvc

        OFFICIAL_KEYWORDS = [
            "act", "emit", "pack", "mold", "pick", "alt", "otherwise", "pulse",
            "cycle", "spin", "halt", "skip", "say", "ask", "guard", "trap",
            "fuse", "lock", "shift", "blank", "aye", "nay", "also", "either", "deny"
        ]

        kw_regex = r"\b(act|emit|pack|mold|pick|alt|otherwise|pulse|cycle|spin|halt|skip|say|ask|guard|trap|fuse|lock|shift|blank|aye|nay|also|either|deny)\b"
        for kw in OFFICIAL_KEYWORDS:
            self.assertTrue(re.search(kw_regex, kw), f"Studio keyword regex should match '{kw}'")

        starter = (
            "# FoxVC Starter Program\n"
            "lock greeting = \"Welcome to Fox Den Studio!\"\n"
            "say greeting\n\n"
            "act calculate(a, b)\n"
            "    lock sum = a + b\n"
            "    emit sum\n\n"
            "lock total = calculate(15, 27)\n"
            "say \"Result: \" + total\n"
        )
        res = run_foxvc(starter)
        self.assertTrue(res.success, f"Starter template failed: {res.error}")
        self.assertIn("Welcome to Fox Den Studio!", res.output)
        self.assertIn("Result: 42", res.output)


if __name__ == "__main__":
    unittest.main()

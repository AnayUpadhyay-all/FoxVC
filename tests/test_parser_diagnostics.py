"""
Tests for Milestone 2.3: Parser Reliability & Structured Diagnostics
Verifies instance-level ParserError state, indentation rules, tab expansion,
error coordinates, and structured diagnostic metadata.
"""

import unittest
from engine.lexer import Lexer, LexerError
from engine.parser import Parser, ParserError
from engine.runner import run_foxvc


class TestParserDiagnostics(unittest.TestCase):
    def test_parser_error_instance_isolation(self):
        """Verify ParserError does not rely on shared class state."""
        source1 = "say 1\nsay 2\nx = +\n"
        source2 = "x = 10\ny = 20\nz = *\n"
        
        # Parse source1
        tokens1 = Lexer(source1, filename="file1.fox").tokenize()
        try:
            Parser(tokens1, filename="file1.fox", source=source1).parse()
        except ParserError as pe1:
            self.assertEqual(pe1.filename, "file1.fox")
            self.assertEqual(pe1.line, 3)

        # Parse source2
        tokens2 = Lexer(source2, filename="file2.fox").tokenize()
        try:
            Parser(tokens2, filename="file2.fox", source=source2).parse()
        except ParserError as pe2:
            self.assertEqual(pe2.filename, "file2.fox")
            self.assertEqual(pe2.line, 3)

    def test_tab_indentation_expansion(self):
        """Verify tab-indented blocks tokenize and parse cleanly."""
        code = "act add_one(n)\n\temit n + 1\n\nres = add_one(5)\nemit res\n"
        res = run_foxvc(code, engine_mode="interp", as_result=True)
        self.assertTrue(res.success)
        self.assertEqual(res.value, 6)

    def test_inconsistent_unindent_rejection(self):
        """Verify inconsistent dedent level raises a clear LexerError."""
        bad_code = "act test()\n    x = 1\n  y = 2\n"
        with self.assertRaises(LexerError) as ctx:
            Lexer(bad_code, filename="bad_indent.fox").tokenize()
        self.assertIn("Indentation error", str(ctx.exception))
        self.assertIn("bad_indent.fox", str(ctx.exception))

    def test_say_rejects_comma_with_friendly_fix(self):
        """Verify say statement with comma is rejected with helpful guidance."""
        bad_say = 'say "hello", "world"'
        tokens = Lexer(bad_say, filename="say_test.fox").tokenize()
        with self.assertRaises(ParserError) as ctx:
            Parser(tokens, filename="say_test.fox", source=bad_say).parse()
        self.assertIn("Commas are not used with 'say'", str(ctx.exception))

    def test_structured_diagnostics_on_result(self):
        """Verify execution result diagnostics list has structured Diagnostic objects."""
        bad_code = "x = 10 +\n"
        res = run_foxvc(bad_code, engine_mode="interp", as_result=True)
        self.assertFalse(res.success)
        self.assertGreater(len(res.diagnostics), 0)
        diag = res.diagnostics[0]
        self.assertEqual(diag.category, "SYNTAX")
        self.assertIsNotNone(diag.message)
        self.assertEqual(res.metadata.get("language_version"), "1.0.0")
        self.assertEqual(res.metadata.get("engine_version"), "0.6.0-alpha")


if __name__ == "__main__":
    unittest.main()

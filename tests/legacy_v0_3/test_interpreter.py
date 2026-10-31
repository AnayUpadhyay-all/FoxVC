import unittest
from engine.runner import run_foxvc

class TestFoxVCInterpreter(unittest.TestCase):
    def test_say_literal_string(self):
        res = run_foxvc('say "Hello, FoxVC!"')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "Hello, FoxVC!")

    def test_arithmetic_addition_and_multiplication(self):
        res = run_foxvc('say 10 + 20 * 3')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "70")

    def test_division_and_subtraction(self):
        res = run_foxvc('say 100 / 4 - 5')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "20")

    def test_string_concatenation_with_number(self):
        res = run_foxvc('x = 15\nsay "Value: " + x')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "Value: 15")

    def test_variables_scope_and_reuse(self):
        res = run_foxvc('a = 5\nb = a * 2\nsay b')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "10")

    def test_division_by_zero_runtime_error(self):
        res = run_foxvc('x = 10 / 0')
        self.assertFalse(res.success)
        self.assertIn("Division by zero", res.error)

    def test_undefined_variable_error(self):
        res = run_foxvc('say undefined_variable')
        self.assertFalse(res.success)
        self.assertIn("Undefined variable", res.error)

    def test_boolean_comparison_true(self):
        res = run_foxvc('say 10 > 5')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "true")

    def test_boolean_comparison_false(self):
        res = run_foxvc('say 10 == 20')
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "false")

    def test_built_in_math_shelf(self):
        code = '''call shelf "mathx"
say sqrt(16)
say abs(-42)
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        lines = res.output.strip().splitlines()
        self.assertEqual(lines, ["4", "42"])

    def test_built_in_physics_shelf_force(self):
        code = '''shelf "physics"
f = force(50, 2)
say f
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertEqual(res.output.strip(), "100")

    def test_store_statement(self):
        res = run_foxvc('store "user_id" 1001')
        self.assertTrue(res.success)
        self.assertEqual(res.data.get("storage", {}).get("user_id"), 1001)

    def test_state_and_action_statements(self):
        code = '''state count = 0
action increment count set 1
'''
        res = run_foxvc(code)
        self.assertTrue(res.success)
        self.assertEqual(res.web_app.get_state("count"), 0)

    def test_empty_program_succeeds(self):
        res = run_foxvc("")
        self.assertTrue(res.success)
        self.assertEqual(res.output, "")

    def test_whitespace_and_comments_only(self):
        res = run_foxvc("# only comments\n\n   \n# another comment")
        self.assertTrue(res.success)
        self.assertEqual(res.output, "")

if __name__ == '__main__':
    unittest.main()

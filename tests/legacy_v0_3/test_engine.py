"""Automated Tests for FoxVC Engine v0.3.1 (Complete Expression, Value, Logic & Mathematics Foundation)"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.runner import run_foxvc

class TestFoxVCEngine(unittest.TestCase):

    # Base Output and Statements
    def test_say_output(self):
        result = run_foxvc('say "Hello, FoxVC"')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Hello, FoxVC")

    def test_multiple_say(self):
        result = run_foxvc('say "First line"\nsay "Second line"')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "First line\nSecond line")

    def test_unknown_instruction(self):
        result = run_foxvc('tell "Hello"')
        self.assertFalse(result.success)
        self.assertIn("is not a recognized FoxVC instruction", result.error)

    def test_missing_string(self):
        result = run_foxvc('say Hello')
        self.assertFalse(result.success)
        self.assertIn("Unknown name: 'Hello'", result.error)

    def test_empty_program(self):
        result = run_foxvc('')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "")

    def test_comments(self):
        code = '# This is a full-line comment\nsay "Live" # inline comment'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Live")

    # Variables & Basic Calculations
    def test_variables_and_numbers(self):
        code = 'x = 10\ny = 25\nsay x\nsay y'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "10\n25")

    def test_arithmetic_precedence(self):
        code = 'result = 2 + 3 * 4\nsay result'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "14")

    def test_arithmetic_parentheses(self):
        code = 'result = (2 + 3) * 4\nsay result'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "20")

    # Mixed-Type Concatenation
    def test_string_plus_integer(self):
        result = run_foxvc('say "Score: " + 95')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Score: 95")

    def test_string_plus_float(self):
        result = run_foxvc('say "Value: " + 6.25')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Value: 6.25")

    def test_string_plus_boolean(self):
        result = run_foxvc('say "Ready: " + true')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Ready: true")

    def test_variable_plus_string(self):
        code = 'score = 95\nsay "Score: " + score'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Score: 95")

    def test_integer_plus_string(self):
        result = run_foxvc('say 10 + " items"')
        self.assertTrue(result.success)
        self.assertEqual(result.output, "10 items")

    # Error Diagnostics
    def test_division_by_zero(self):
        code = 'x = 10 / 0'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Division by zero error", result.error)

    def test_undefined_variable(self):
        code = 'say unknown_variable'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Unknown name: 'unknown_variable'", result.error)

    def test_invalid_type_addition_without_string(self):
        code = 'x = true + 10'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Cannot add types 'boolean' and 'number'", result.error)

    def test_invalid_string_subtraction(self):
        code = 'x = "10" - 5'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Subtraction '-' requires numbers, found 'text' and 'number'", result.error)

    def test_full_stress_test_program(self):
        code = (
            'x = 12.5\n'
            'y = 4\n'
            'z = (x * 2) + y\n'
            'check = z == 29\n'
            'say "x = " + x\n'
            'say "y = " + y\n'
            'say "z = " + z\n'
            'say "Valid result: " + check\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        expected = "x = 12.5\ny = 4\nz = 29\nValid result: true"
        self.assertEqual(result.output, expected)

    # Python Independence & Strict Type Isolation
    def test_boolean_number_equality_independence(self):
        code = 'say true == 1\nsay false == 0\nsay true != 1\nsay false != 0'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "false\nfalse\ntrue\ntrue")

    def test_cross_type_equality_independence(self):
        code = 'say "10" == 10\nsay true == "true"'
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "false\nfalse")

    def test_boolean_ordering_rejection(self):
        code = 'say false < true'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Cannot compare 'boolean' with 'boolean'", result.error)

    def test_text_multiplication_rejection(self):
        code = 'say "hello" * 3'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Multiplication '*' requires numbers, found 'text' and 'number'", result.error)

    def test_strict_logical_operand_type_check(self):
        code = 'say true and 5'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("'and' requires boolean operands, found 'boolean' and 'number'", result.error)

    def test_unary_not_strict_type_check(self):
        code = 'say not 0'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("'not' requires a boolean (true/false), found number '0'", result.error)

    # Multiline Continuation
    def test_multiline_parenthesized_assignment(self):
        code = (
            'a = 10\n'
            'b = 5\n'
            'c = 2\n'
            'result = (\n'
            '    (a + b) * c\n'
            ')\n'
            'say result\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "30")

    def test_multiline_say_expression(self):
        code = (
            'say (\n'
            '    "Line total: " +\n'
            '    (10 * 5)\n'
            ')\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Line total: 50")

    def test_multiline_complex_nested_math(self):
        code = (
            'x = 10\n'
            'y = 20\n'
            'calc = (\n'
            '    (x * 2) +\n'
            '    (\n'
            '        y / 2\n'
            '    )\n'
            ')\n'
            'say "Result = " + calc\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Result = 30")

    # Interactive User Input
    def test_basic_ask_input(self):
        code = 'name = ask "Your name: "\nsay "Hello, " + name'
        result = run_foxvc(code, input_source=lambda prompt: "Anay")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Hello, Anay")

    def test_ask_empty_input(self):
        code = 'entry = ask "Optional note: "\nsay "Note is empty: " + (entry == "")'
        result = run_foxvc(code, input_source=lambda prompt: "")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Note is empty: true")

    def test_multiple_sequential_inputs(self):
        inputs = iter(["Fox", "Red"])
        code = 'name = ask "Name: "\ncolor = ask "Color: "\nsay name + " is " + color'
        result = run_foxvc(code, input_source=lambda prompt: next(inputs))
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Fox is Red")

    def test_ask_input_type_is_always_text(self):
        code = 'digits = ask "Enter pin: "\nx = digits - 5'
        result = run_foxvc(code, input_source=lambda prompt: "1234")
        self.assertFalse(result.success)
        self.assertIn("Subtraction '-' requires numbers, found 'text' and 'number'", result.error)

    def test_ask_input_in_comparison(self):
        code = 'choice = ask "Confirm (yes/no): "\nsay choice == "yes"'
        result = run_foxvc(code, input_source=lambda prompt: "yes")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "true")

    # Punctuation Rejections
    def test_comma_rejection_diagnostic(self):
        code = 'say "Hello", "World"'
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Commas are not used in FoxVC syntax", result.error)

    def test_apostrophe_rejection_diagnostic(self):
        code = "say 'Single quote string'"
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Apostrophes are not used for text in FoxVC", result.error)

    def test_semicolon_rejection_diagnostic(self):
        code = "x = 10;\nsay x"
        result = run_foxvc(code)
        self.assertFalse(result.success)
        self.assertIn("Semicolons are not used in FoxVC", result.error)

    # v0.3.1 Numbers, Precision, Floats & Extremes
    def test_extreme_large_and_small_numbers(self):
        code = (
            'large = 1000000000000\n'
            'small = 0.000000001\n'
            'result = large * small\n'
            'say result\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "1000")

    def test_division_precision_and_normalization(self):
        code = (
            'x = 1\n'
            'y = 2\n'
            'say x / y\n'
            'say 10 / 3\n'
            'say 22 / 7\n'
            'say 120 / 8\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        lines = result.output.split("\n")
        self.assertEqual(lines[0], "0.5")
        self.assertTrue(lines[1].startswith("3.33333"))
        self.assertTrue(lines[2].startswith("3.142857"))
        self.assertEqual(lines[3], "15")

    def test_floating_point_drift_normalization(self):
        code = (
            'a = 0.1\n'
            'b = 0.2\n'
            'say a + b\n'
            'say (0.1 + 0.2) == 0.3\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "0.3\ntrue")

    def test_zero_identity(self):
        code = (
            'x = 0\n'
            'say x == 0\n'
            'say x == false\n'
            'say x + 5\n'
            'say x * 100\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "true\nfalse\n5\n0")

    # v0.3.1 Reassignment & Long Chains
    def test_variable_reassignment_accumulator(self):
        code = (
            'x = 10\n'
            'x = x + 5\n'
            'x = x * 2\n'
            'x = x - 3\n'
            'say x\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "27")

    def test_ten_step_dependency_chain(self):
        code = (
            'a = 5\n'
            'b = a * 4\n'
            'c = b + 10\n'
            'd = c / 2\n'
            'e = d * 7\n'
            'f = e - 3\n'
            'g = f * 2\n'
            'h = g / 5\n'
            'i = h + e\n'
            'j = i * 3\n'
            'say j\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "437.4")

    def test_calculated_values_first_class_reuse(self):
        code = (
            'distance = 120\n'
            'time = 8\n'
            'speed = distance / time\n'
            'trip1 = speed * 2\n'
            'trip2 = speed * 5\n'
            'trip3 = speed * 10\n'
            'say trip1\n'
            'say trip2\n'
            'say trip3\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "30\n75\n150")

    # v0.3.1 Comparisons with Expressions & Nested Logic
    def test_comparisons_with_expressions_both_sides(self):
        code = (
            'a = 10\n'
            'b = 5\n'
            'c = 3\n'
            'd = 4\n'
            'say (a + b) > (c * d)\n'
            'say a + b > c * d\n'
            'say (a * 2) == (b * 4)\n'
            'say (a - b) <= (c + d)\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "true\ntrue\ntrue\ntrue")

    def test_nested_boolean_precedence_and_grouping(self):
        code = (
            'age = 15\n'
            'score = 85\n'
            'active = true\n'
            'say (age > 10 and score > 50) or active\n'
            'say not ((age > 10) and (score < 50))\n'
            'say true or false and false\n'
            'say (true or false) and false\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "true\ntrue\ntrue\nfalse")

    # v0.3.1 Real-World Science, Geometry, Finance & Statistics
    def test_physics_kinematics_and_energy(self):
        code = (
            'initial_velocity = 10\n'
            'acceleration = 9.8\n'
            'time = 4\n'
            'final_velocity = initial_velocity + (acceleration * time)\n'
            'distance = (initial_velocity * time) + (0.5 * acceleration * (time * time))\n'
            'mass = 12\n'
            'ke = (mass * (final_velocity * final_velocity)) / 2\n'
            'say final_velocity\n'
            'say distance\n'
            'say ke\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "49.2\n118.4\n14523.84")

    def test_geometry_formulas(self):
        code = (
            'base = 20\n'
            'height = 15\n'
            'triangle_area = (base * height) / 2\n'
            'radius = 5\n'
            'cylinder_height = 10\n'
            'pi = 3.14159\n'
            'cylinder_vol = pi * (radius * radius) * cylinder_height\n'
            'say triangle_area\n'
            'say cylinder_vol\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "150\n785.3975")

    def test_finance_interest_and_discount(self):
        code = (
            'price = 5000\n'
            'discount = 10\n'
            'saved = (price * discount) / 100\n'
            'final_price = price - saved\n'
            'annual_rate = 0.08\n'
            'interest = final_price * annual_rate * 2\n'
            'say final_price\n'
            'say interest\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "4500\n720")

    def test_statistics_mean_and_deviations(self):
        code = (
            'x1 = 20\n'
            'x2 = 40\n'
            'x3 = 60\n'
            'total = x1 + x2 + x3\n'
            'mean = total / 3\n'
            'dev1 = x1 - mean\n'
            'dev3 = x3 - mean\n'
            'say mean\n'
            'say dev1\n'
            'say dev3\n'
        )
        result = run_foxvc(code)
        self.assertTrue(result.success)
        self.assertEqual(result.output, "40\n-20\n20")

if __name__ == "__main__":
    unittest.main()

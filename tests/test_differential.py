"""
Differential Testing Suite for FoxVC Execution Engines
Verifies semantic equivalence between:
- Tree-Walking Interpreter ('interp')
- Pure Python Register Bytecode VM ('vm')
- Native C Extension Virtual Machine ('fast')
"""

import unittest
from typing import Any
from engine.runner import run_foxvc


class TestDifferentialExecution(unittest.TestCase):
    """
    Validates that identical valid FoxVC programs produce identical results
    across supported execution engines on their documented common subset.
    """

    def _assert_three_way_match(self, code: str, expected_val: Any, description: str):
        """Runs code through interp, vm, and fast, asserting identical scalar output."""
        res_interp = run_foxvc(code, engine_mode='interp', as_result=True)
        res_vm = run_foxvc(code, engine_mode='vm', as_result=True)
        res_fast = run_foxvc(code, engine_mode='fast', as_result=True, allow_fallback=False)

        self.assertTrue(res_interp.success, f"Interpreter failed on {description}: {res_interp.error}")
        self.assertTrue(res_vm.success, f"Python VM failed on {description}: {res_vm.error}")
        self.assertTrue(res_fast.success, f"Native C VM failed on {description}: {res_fast.error}")

        self.assertEqual(res_interp.value, expected_val, f"Interp return mismatch on {description}")
        self.assertEqual(res_vm.value, expected_val, f"VM return mismatch on {description}")
        self.assertEqual(res_fast.value, expected_val, f"Fast return mismatch on {description}")

    def _assert_two_way_match(self, code: str, expected_val: Any, description: str):
        """Runs code through interp and vm (for features not supported by Native C VM)."""
        res_interp = run_foxvc(code, engine_mode='interp', as_result=True)
        res_vm = run_foxvc(code, engine_mode='vm', as_result=True)

        self.assertTrue(res_interp.success, f"Interpreter failed on {description}: {res_interp.error}")
        self.assertTrue(res_vm.success, f"Python VM failed on {description}: {res_vm.error}")

        self.assertEqual(res_interp.value, expected_val, f"Interp return mismatch on {description}")
        self.assertEqual(res_vm.value, expected_val, f"VM return mismatch on {description}")

    # =========================================================================
    # Common Subset: 3-Way Differential Tests (Interp == VM == Fast)
    # =========================================================================

    def test_arithmetic_precedence_and_operations(self):
        code = """
x = 15 + 5 * 4 - 10 / 2
emit x
"""
        # 15 + 20 - 5 = 30
        self._assert_three_way_match(code, 30.0, "Arithmetic precedence")

    def test_variable_reassignment_and_mutation(self):
        code = """
a = 10
b = 20
a = a + b
b = a * 2
emit a + b
"""
        # a=30, b=60, a+b=90
        self._assert_three_way_match(code, 90.0, "Variable mutation")

    def test_conditional_pick_otherwise(self):
        code = """
x = 42
result = 0
pick x > 50
    result = 100
otherwise
    result = 200
emit result
"""
        self._assert_three_way_match(code, 200.0, "Pick-otherwise branching")

    def test_count_loop_cycle_accumulation(self):
        code = """
total = 0
cycle i 5
    total = total + i
emit total
"""
        # 0 + 1 + 2 + 3 + 4 = 10
        self._assert_three_way_match(code, 10.0, "Cycle loop accumulation")

    # =========================================================================
    # Higher-Level Features: 2-Way Differential Tests (Interp == VM)
    # =========================================================================

    def test_function_definition_and_call(self):
        code = """
act multiply(a, b)
    emit a * b

emit multiply(7, 6)
"""
        self._assert_two_way_match(code, 42.0, "Function call and emit")

    def test_recursive_function(self):
        code = """
act fib(n)
    pick n <= 1
        emit n
    otherwise
        emit fib(n - 1) + fib(n - 2)

emit fib(8)
"""
        # fib(8) = 21
        self._assert_two_way_match(code, 21.0, "Recursive fibonacci")

    def test_mold_blueprint_property_access(self):
        code = """
mold Point {
    x: 10
    y: 20
}

pt = Point()
pt.x = 50
emit pt.x + pt.y
"""
        self._assert_two_way_match(code, 70.0, "Mold blueprint instantiation and property update")

    def test_trap_block_isolation(self):
        code = """
flag = 0
trap
    guard nay
otherwise
    flag = 99
emit flag
"""
        self._assert_two_way_match(code, 99.0, "Trap block isolation")

    # =========================================================================
    # Capability Detection & Explicit Rejection Tests
    # =========================================================================

    def test_native_vm_rejects_unsupported_dynamic_code(self):
        """Confirms Native C VM cleanly rejects code it cannot accelerate when allow_fallback=False."""
        code = """
mold Player {
    score: 100
}
p = Player()
emit p.score
"""
        res_fast = run_foxvc(code, engine_mode='fast', as_result=True, allow_fallback=False)
        self.assertFalse(res_fast.success, "Fast mode must not claim success for unsupported molds")
        self.assertIn("cannot accelerate", str(res_fast.error))

    def test_native_vm_explicit_fallback_opt_in(self):
        """Confirms that when allow_fallback=True is passed, fallback to FoxVM works explicitly."""
        code = """
mold Player {
    score: 100
}
p = Player()
emit p.score
"""
        res_fast = run_foxvc(code, engine_mode='fast', as_result=True, allow_fallback=True)
        self.assertTrue(res_fast.success, "Fast mode with explicit fallback should succeed on FoxVM")
        self.assertEqual(res_fast.value, 100.0)
        self.assertEqual(res_fast.engine, "vm")


if __name__ == '__main__':
    unittest.main()

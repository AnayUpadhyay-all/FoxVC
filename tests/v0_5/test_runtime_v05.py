import unittest
from engine.lexer import Lexer
from engine.parser import Parser
from engine.interpreter import Interpreter

class TestFoxVCRuntimeV05(unittest.TestCase):
    def setUp(self):
        self.interp = Interpreter()

    def run_code(self, src):
        tokens = Lexer(src).tokenize()
        ast = Parser(tokens, source=src).parse()
        self.interp.reset()
        self.interp.execute(ast)
        return self.interp

    # Wave 3.1: Short-circuit tests
    def test_short_circuit_also(self):
        src = """
guard_passed = 0
pick 1 == 2 also (10 / 0 == 5)
    guard_passed = 0
otherwise
    guard_passed = 1
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('guard_passed'), 1)

    def test_short_circuit_either(self):
        src = """
either_passed = 0
pick 1 == 1 either (10 / 0 == 5)
    either_passed = 1
otherwise
    either_passed = 0
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('either_passed'), 1)

    # Wave 3.2: Control flow signals bypassing trap
    def test_trap_emit_bypass(self):
        src = """
act test_emit()
    trap
        emit 42
    otherwise
        emit 0

ans = test_emit()
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('ans'), 42)

    def test_trap_halt_bypass(self):
        src = """
count = 0
trap_triggered = 0
pulse dt
    count = count + 1
    trap
        halt
    otherwise
        trap_triggered = 1
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('trap_triggered'), 0)
        self.assertEqual(it.variables.get('count'), 1)

    def test_trap_catches_actual_error(self):
        src = """
error_caught = 0
trap
    bad = 10 / 0
otherwise
    error_caught = 1
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('error_caught'), 1)


    # Wave 3.4 & 3.5: Scope isolation & recursion tests
    def test_outer_scope_mutation(self):
        src = """
score = 0
act add_score()
    score = score + 10

add_score()
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('score'), 10)

    def test_local_variable_no_leak(self):
        src = """
act compute()
    local_temp = 999
    emit local_temp

ans = compute()
"""
        it = self.run_code(src)
        self.assertNotIn('local_temp', it.variables)

    def test_recursion_call_frame_isolation(self):
        src = """
act factorial(n)
    pick n <= 1
        emit 1
    emit n * factorial(n - 1)

fact5 = factorial(5)
"""
        it = self.run_code(src)
        self.assertEqual(it.variables.get('fact5'), 120)

if __name__ == '__main__':
    unittest.main()

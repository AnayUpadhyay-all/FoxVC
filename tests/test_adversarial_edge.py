"""
FoxVC Adversarial Edge-Case Suite
Validates deep recursion, nested error traps, zero-iteration loops, and mold mutations.
"""
import unittest
from engine.runner import run_foxvc


class TestAdversarialEdge(unittest.TestCase):
    def test_double_nested_trap_isolation(self):
        code = """
outer_flag = 0
inner_flag = 0

trap
    trap
        guard nay
    otherwise
        inner_flag = 1
    # Outer guard still runs
    guard nay
otherwise
    outer_flag = 2

emit outer_flag + inner_flag
"""
        res = run_foxvc(code, engine_mode="vm", as_result=False)
        self.assertEqual(res, 3)

    def test_deep_recursion_callframe_integrity(self):
        code = """
act countdown(n)
    pick n <= 0
        emit 0
    otherwise
        emit 1 + countdown(n - 1)

emit countdown(40)
"""
        res = run_foxvc(code, engine_mode="vm", as_result=False)
        self.assertEqual(res, 40)

    def test_zero_iteration_loops_and_empty_list(self):
        code = """
items = []
count = 0
cycle i 0
    count = count + 1
spin nay
    count = count + 10
emit count
"""
        res = run_foxvc(code, engine_mode="vm", as_result=False)
        self.assertEqual(res, 0)

    def test_nested_mold_mutations(self):
        code = """
mold Weapon {
    damage: 25
}
mold Player {
    w: 0
}

p = Player()
p.w = Weapon()
p.w.damage = 75
emit p.w.damage
"""
        res = run_foxvc(code, engine_mode="vm", as_result=False)
        self.assertEqual(res, 75)

    def test_conditional_loop_halt(self):
        code = """
acc = 0
cycle i 10
    pick i == 5
        halt
    acc = acc + 1
emit acc
"""
        res = run_foxvc(code, engine_mode="vm", as_result=False)
        self.assertEqual(res, 5)


if __name__ == "__main__":
    unittest.main()

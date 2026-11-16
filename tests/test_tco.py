"""
FoxVC 2.0 / Engine 0.7.0 Tail-Call Optimization (TCO) Test Suite
Verifies that recursive tail calls execute in O(1) stack space,
allowing recursion depths far exceeding MAX_CALL_STACK (1024) without stack overflow.
"""
import unittest
from engine.c_vm import FoxCVM


class TestTailCallOptimization(unittest.TestCase):
    def setUp(self):
        self.cvm = FoxCVM()
        self.cvm.lib.reset_memory_arena()

    def tearDown(self):
        self.cvm.lib.reset_memory_arena()

    def test_deep_tail_recursion_50000(self):
        """Tail-call recursion of depth 50,000 (exceeds 1024 frame limit by 50x)."""
        inst = [
            # countdown(r0):
            13, 1, 0, 0,     # 0: CMP_LE r1 = (r0 <= 0.0)
            16, 1, 12,       # 4: JUMP_IF_FALSE if !r1 goto 12
            1, 2, 0,         # 7: LOAD_CONST r2 = 0.0
            20, 2,           # 10: RETURN r2
            5, 3, 0, 1,      # 12: SUB r3 = r0 - 1.0
            19, 0, 1, 4, 3,  # 16: CALL f_addr=0, argc=1, dst=4, arg0=r3
            20, 4,           # 21: RETURN r4 (TAIL CALL - frame is reused!)
            # Top-level:
            1, 0, 2,         # 23: LOAD_CONST r0 = 50000.0
            19, 0, 1, 5, 0,  # 26: CALL f_addr=0, argc=1, dst=5, arg0=r0
            17               # 31: HALT
        ]
        nums = [0.0, 1.0, 50000.0]
        res = self.cvm.run_flat(inst, nums, [])
        self.assertEqual(res, 0.0, "Tail-call optimization must handle 50,000 calls without overflow")

    def test_deep_tail_recursion_100000(self):
        """Tail-call recursion of depth 100,000."""
        inst = [
            13, 1, 0, 0,     # 0: CMP_LE r1 = (r0 <= 0.0)
            16, 1, 12,       # 4: JUMP_IF_FALSE if !r1 goto 12
            1, 2, 0,         # 7: LOAD_CONST r2 = 0.0
            20, 2,           # 10: RETURN r2
            5, 3, 0, 1,      # 12: SUB r3 = r0 - 1.0
            19, 0, 1, 4, 3,  # 16: CALL f_addr=0, argc=1, dst=4, arg0=r3
            20, 4,           # 21: RETURN r4
            1, 0, 2,         # 23: LOAD_CONST r0 = 100000.0
            19, 0, 1, 5, 0,  # 26: CALL f_addr=0, argc=1, dst=5, arg0=r0
            17               # 31: HALT
        ]
        nums = [0.0, 1.0, 100000.0]
        res = self.cvm.run_flat(inst, nums, [])
        self.assertEqual(res, 0.0, "Tail-call recursion must complete 100,000 depth in O(1) stack")


if __name__ == "__main__":
    unittest.main()

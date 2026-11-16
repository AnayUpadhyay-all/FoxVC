"""
FoxVC Tiered Chained Memory Arena & Safety Trap Test Suite
Tests:
1. Primary 8MB arena allocation (Tier 1)
2. Standby 8MB pre-warmed arena rollover (Tier 2)
3. Dynamic chained arena chunks (Tier 3)
4. Memory Safety Ceiling trap at 64MB (Tier 4)
5. Dynamic pack table capacity scaling beyond 4096 packs
"""
import unittest
import ctypes
import os

from engine.c_vm import FoxCVM, Op


class TestTieredMemoryArena(unittest.TestCase):
    def setUp(self):
        self.cvm = FoxCVM()
        # Ensure clean arena state
        self.cvm.lib.reset_memory_arena()

    def tearDown(self):
        self.cvm.lib.reset_memory_arena()

    def test_tier1_primary_allocation(self):
        """Tier 1: Allocate packs within the initial 8MB primary arena."""
        # 100 packs of 1000 doubles (8000 bytes each) = 800 KB
        for i in range(100):
            pid = self.cvm.lib.allocate_pack(1000)
            self.assertEqual(pid, i)

    def test_tier2_standby_arena_rollover(self):
        """Tier 2: Rollover seamlessly from Primary 8MB to Standby 8MB."""
        # Allocate ~6 MB in primary
        # 6 * 1024 * 1024 / 8 = 786432 doubles
        pid1 = self.cvm.lib.allocate_pack(786432)
        self.assertEqual(pid1, 0)

        # Allocate another 6 MB -> Should cleanly roll over into Standby 8MB arena
        pid2 = self.cvm.lib.allocate_pack(786432)
        self.assertEqual(pid2, 1)

    def test_tier3_dynamic_chained_chunks(self):
        """Tier 3: Expand past 16MB into dynamically chained chunks."""
        # Allocate across 3 chunks of 6MB each (total 18MB > 16MB)
        # Primary: 6MB, Standby: 6MB, Dynamic Chunk 1: 6MB
        pid0 = self.cvm.lib.allocate_pack(786432)
        pid1 = self.cvm.lib.allocate_pack(786432)
        pid2 = self.cvm.lib.allocate_pack(786432)

        self.assertEqual(pid0, 0)
        self.assertEqual(pid1, 1)
        self.assertEqual(pid2, 2)

    def test_tier4_safety_ceiling_trap(self):
        """Tier 4: Trigger safety trap when exceeding 64MB memory ceiling."""
        # Each 786432 doubles = 6 MB.
        # 10 allocations = 60 MB (succeeds)
        # 12 allocations = 72 MB (exceeds 64MB ceiling -> safety trap protects OS)
        allocated = 0
        trap_triggered = False
        for i in range(15):
            pid = self.cvm.lib.allocate_pack(786432)
            if pid < 0:
                trap_triggered = True
                break
            allocated += 1

        self.assertTrue(trap_triggered, "Memory Safety Trap must trigger when exceeding 64MB ceiling")
        self.assertGreaterEqual(allocated, 8, "Must allocate at least 8 chunks (48+ MB) before ceiling")

    def test_dynamic_pack_table_scaling(self):
        """Pack table dynamically scales past INITIAL_PACK_CAPACITY (4096) up to 5000+."""
        # Allocate 5000 small packs (exceeds the old static limit of 4096)
        total_packs = 5000
        for i in range(total_packs):
            pid = self.cvm.lib.allocate_pack(16)
            self.assertEqual(pid, i, f"Pack {i} allocation failed during dynamic table expansion")

    def test_bytecode_execution_with_tiered_arena(self):
        """Execute bytecode using FoxCVM ensuring full lifecycle reset."""
        instructions = [
            (Op.LOAD_CONST, 0, 42.0),
            (Op.BUILD_PACK, 1, [("value", 0)]),
            (Op.GET_MEMBER, 2, 1, "value"),
            (Op.RETURN, 2),
            (Op.HALT,)
        ]
        flat, nums, strs = self.cvm.compile_payload((instructions, {}))
        result = self.cvm.run_flat(flat, nums, strs)
        self.assertEqual(result, 42.0)


if __name__ == "__main__":
    unittest.main()

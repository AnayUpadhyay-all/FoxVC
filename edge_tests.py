import sys
import os
sys.path.insert(0, "/home/anay/Desktop/FoxVC")
from engine.runner import run_foxvc

print("=" * 60)
print("🥊 LAUNCHING FOXVC ADVERSARIAL EDGE-CASE SUITE")
print("=" * 60)

passed = 0

# TEST 1: Double-Nested Trap
code1 = """
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
res1 = run_foxvc(code1, engine_mode="vm")
assert res1 == 3, f"Test 1 failed! Got {res1}"
print("✅ Test 1: Double-nested trap isolation passed (Result: 3)")
passed += 1

# TEST 2: Deep Recursion CallFrame integrity
code2 = """
act countdown(n)
    pick n <= 0
        emit 0
    otherwise
        emit 1 + countdown(n - 1)

emit countdown(40)
"""
res2 = run_foxvc(code2, engine_mode="vm")
assert res2 == 40, f"Test 2 failed! Got {res2}"
print("✅ Test 2: Deep CallFrame recursion (depth 40) passed")
passed += 1

# TEST 3: Zero-iteration loops & empty lists
code3 = """
items = []
count = 0
cycle i 0
    count = count + 1
spin nay
    count = count + 10
emit count
"""
res3 = run_foxvc(code3, engine_mode="vm")
assert res3 == 0, f"Test 3 failed! Got {res3}"
print("✅ Test 3: Zero-iteration loops & empty list passed")
passed += 1

# TEST 4: Nested mold property overrides
code4 = """
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
res4 = run_foxvc(code4, engine_mode="vm")
assert res4 == 75, f"Test 4 failed! Got {res4}"
print("✅ Test 4: Nested Mold mutations passed (Result: 75)")
passed += 1

# TEST 5: Halting from deeply nested branch inside loop
code5 = """
acc = 0
cycle i 10
    pick i == 5
        halt
    acc = acc + 1
emit acc
"""
res5 = run_foxvc(code5, engine_mode="vm")
assert res5 == 5, f"Test 5 failed! Got {res5}"
print("✅ Test 5: Conditional loop halt passed (Result: 5)")
passed += 1

print("=" * 60)
print(f"🏆 ALL {passed}/5 ADVERSARIAL TESTS PASSED CLEANLY!")
print("=" * 60)

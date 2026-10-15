import os
import ctypes
from engine.bytecode import Op

class CFoxInstruction(ctypes.Structure):
    _fields_ = [
        ('op', ctypes.c_int32),
        ('a', ctypes.c_int32),
        ('b', ctypes.c_int32),
        ('c', ctypes.c_int32),
        ('val', ctypes.c_double),
    ]

OP_TO_C = {
    Op.LOAD_CONST: 1,
    Op.LOAD_VAR: 2,
    Op.STORE_VAR: 3,
    Op.ADD: 4,
    Op.SUB: 5,
    Op.MUL: 6,
    Op.DIV: 7,
    Op.MOD: 8,
    Op.CMP_EQ: 9,
    Op.CMP_NE: 10,
    Op.CMP_LT: 11,
    Op.CMP_GT: 12,
    Op.CMP_LE: 13,
    Op.CMP_GE: 14,
    Op.LOGIC_NOT: 15,
    Op.JUMP: 16,
    Op.JUMP_IF_FALSE: 17,
    Op.GET_TIME: 18,
    Op.EMIT: 19,
    Op.HALT: 20
}

class FoxCVM:
    def __init__(self):
        so_path = os.path.join(os.path.dirname(__file__), 'foxvm.so')
        self.lib = ctypes.CDLL(so_path)
        self.lib.run_vm_c.argtypes = [ctypes.POINTER(CFoxInstruction), ctypes.c_int]
        self.lib.run_vm_c.restype = ctypes.c_double

    @staticmethod
    def can_accelerate(instructions, functions) -> bool:
        """Returns True if code is pure numeric/control flow suitable for the C engine."""
        if functions:
            return False
        for inst in instructions:
            op = inst[0]
            if op not in OP_TO_C:
                return False
            if op == Op.LOAD_CONST and not isinstance(inst[2], (int, float, bool)):
                return False
        return True

    def run(self, instructions):
        n = len(instructions)
        c_code = (CFoxInstruction * n)()
        var_map = {}

        for i, inst in enumerate(instructions):
            op = inst[0]
            c_op = OP_TO_C.get(op, 20)
            a = b = c = 0
            val = 0.0

            if op == Op.LOAD_CONST:
                a = inst[1]
                val = float(inst[2])
            elif op == Op.LOAD_VAR:
                a = inst[1]
                var_name = inst[2]
                if var_name not in var_map:
                    var_map[var_name] = len(var_map)
                b = var_map[var_name]
            elif op == Op.STORE_VAR:
                var_name = inst[1]
                if var_name not in var_map:
                    var_map[var_name] = len(var_map)
                a = var_map[var_name]
                b = inst[2]
            elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD,
                        Op.CMP_EQ, Op.CMP_NE, Op.CMP_LT, Op.CMP_GT, Op.CMP_LE, Op.CMP_GE):
                a = inst[1]
                b = inst[2]
                c = inst[3]
            elif op == Op.LOGIC_NOT:
                a = inst[1]
                b = inst[2]
            elif op == Op.JUMP:
                a = inst[1]
            elif op == Op.JUMP_IF_FALSE:
                a = inst[1]
                b = inst[2]
            elif op == Op.GET_TIME:
                a = inst[1]
            elif op == Op.EMIT:
                a = inst[1]

            c_code[i] = CFoxInstruction(c_op, a, b, c, val)

        res = self.lib.run_vm_c(c_code, n)
        return int(res) if res.is_integer() else res

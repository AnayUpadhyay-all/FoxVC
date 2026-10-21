import os
import struct
import ctypes
from engine.bytecode import Op


def serialize_foxc(filepath: str, flat_inst: list, num_consts: list, str_consts: list):
    """
    Binary format (.foxc):
    - Magic: b'FOXC' (4 bytes)
    - Version: uint32 (1)
    - len(flat_inst): uint32 + int32 elements
    - len(num_consts): uint32 + float64 elements
    - len(str_consts): uint32 + (uint32 len + utf8 bytes)
    """
    with open(filepath, 'wb') as f:
        f.write(b'FOXC')
        f.write(struct.pack('<I', 1))

        # flat_inst
        f.write(struct.pack('<I', len(flat_inst)))
        if flat_inst:
            f.write(struct.pack(f'<{len(flat_inst)}i', *flat_inst))

        # num_consts
        f.write(struct.pack('<I', len(num_consts)))
        if num_consts:
            f.write(struct.pack(f'<{len(num_consts)}d', *num_consts))

        # str_consts
        f.write(struct.pack('<I', len(str_consts)))
        for s in str_consts:
            encoded = s.encode('utf-8')
            f.write(struct.pack('<I', len(encoded)))
            f.write(encoded)


def deserialize_foxc(filepath: str):
    """Reads a binary .foxc bytecode cache file."""
    with open(filepath, 'rb') as f:
        magic = f.read(4)
        if magic != b'FOXC':
            raise ValueError(f"Invalid .foxc magic header: {magic}")
        version, = struct.unpack('<I', f.read(4))
        if version != 1:
            raise ValueError(f"Unsupported .foxc version: {version}")

        n_inst, = struct.unpack('<I', f.read(4))
        flat_inst = list(struct.unpack(f'<{n_inst}i', f.read(4 * n_inst))) if n_inst else []

        n_nums, = struct.unpack('<I', f.read(4))
        num_consts = list(struct.unpack(f'<{n_nums}d', f.read(8 * n_nums))) if n_nums else []

        n_strs, = struct.unpack('<I', f.read(4))
        str_consts = []
        for _ in range(n_strs):
            slen, = struct.unpack('<I', f.read(4))
            str_consts.append(f.read(slen).decode('utf-8'))

    return flat_inst, num_consts, str_consts


class FoxCVM:
    def __init__(self):
        so_path = os.path.join(os.path.dirname(__file__), 'foxvm.so')
        if not os.path.exists(so_path):
            raise FileNotFoundError(f"Native binary not found at {so_path}. Build it using gcc first!")
        
        self.lib = ctypes.CDLL(so_path)
        
        # Matches C signature:
        # double run_bytecode(int* inst, int inst_len, double* num_consts, int num_consts_len, const char** str_consts, int str_consts_len)
        self.lib.run_bytecode.argtypes = [
            ctypes.POINTER(ctypes.c_int32),
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_double),
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.c_int32
        ]
        self.lib.run_bytecode.restype = ctypes.c_double

    @staticmethod
    def can_accelerate(instructions, functions) -> bool:
        """Returns True if the bytecode payload is suitable for native C execution."""
        return True

    def compile_payload(self, code_pkg):
        instructions = code_pkg[0] if isinstance(code_pkg, (tuple, list)) and len(code_pkg) > 0 and isinstance(code_pkg[0], list) else code_pkg

        flat_inst = []
        num_consts = []
        str_consts = []

        def get_num_idx(val):
            v = float(val)
            if v in num_consts:
                return num_consts.index(v)
            num_consts.append(v)
            return len(num_consts) - 1

        def get_str_idx(val):
            s = str(val)
            if s in str_consts:
                return str_consts.index(s)
            str_consts.append(s)
            return len(str_consts) - 1

        # Opcodes matching engine/foxvm.c
        op_map = {
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
            Op.JUMP: 15,
            Op.JUMP_IF_FALSE: 16,
            Op.HALT: 17,
            Op.GET_TIME: 18,
            Op.CALL: 19,
            Op.RETURN: 20,
            Op.PRINT: 21,
            Op.EMIT: 22,
            Op.SIN: 24,
            Op.COS: 25,
            Op.SQRT: 26,
            Op.RND: 27,
            Op.BUILD_LIST: 28,
            Op.GET_INDEX: 29,
            Op.SET_INDEX: 30
        }

        var_map = {}
        str_regs = {}
        str_vars = {}

        # Precompute flat offset for each instruction so JUMP targets match flat bytecode IPs
        inst_to_flat = {}
        flat_len = 0
        for i, inst in enumerate(instructions):
            inst_to_flat[i] = flat_len
            op = inst[0]
            opcode_num = op_map.get(op, 0)
            if opcode_num == 0:
                continue
            if op == Op.LOAD_CONST:
                flat_len += 3
            elif op in (Op.LOAD_VAR, Op.STORE_VAR):
                flat_len += 3
            elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD,
                        Op.CMP_EQ, Op.CMP_NE, Op.CMP_LT, Op.CMP_GT, Op.CMP_LE, Op.CMP_GE):
                flat_len += 4
            elif op == Op.JUMP:
                flat_len += 2
            elif op == Op.JUMP_IF_FALSE:
                flat_len += 3
            elif op == Op.PRINT:
                flat_len += 3
            elif op == Op.EMIT:
                flat_len += 2
            elif op == Op.HALT:
                flat_len += 1
            elif op in (Op.GET_TIME, Op.RND, Op.RETURN):
                flat_len += 2
            elif op in (Op.SIN, Op.COS, Op.SQRT):
                flat_len += 3
            elif op == Op.CALL:
                args = inst[3] if len(inst) > 3 else []
                flat_len += 4 + len(args)
            elif op == Op.BUILD_LIST:
                elements = inst[2] if len(inst) > 2 else []
                flat_len += 4 + len(elements)
            elif op in (Op.GET_INDEX, Op.SET_INDEX):
                flat_len += 4
            else:
                flat_len += 1
        inst_to_flat[len(instructions)] = flat_len

        for inst in instructions:
            op = inst[0]
            opcode_num = op_map.get(op, 0)
            if opcode_num == 0:
                continue

            flat_inst.append(opcode_num)

            if op == Op.LOAD_CONST:
                r, val = inst[1], inst[2]
                if isinstance(val, str):
                    s_idx = get_str_idx(val)
                    str_regs[r] = s_idx
                    flat_inst.extend([r, get_num_idx(0.0)])
                else:
                    str_regs.pop(r, None)
                    flat_inst.extend([r, get_num_idx(val if isinstance(val, (int, float, bool)) else 0.0)])
            elif op == Op.LOAD_VAR:
                dst = inst[1]
                var_name = inst[2]
                if var_name in str_vars:
                    str_regs[dst] = str_vars[var_name]
                else:
                    str_regs.pop(dst, None)
                if var_name not in var_map:
                    var_map[var_name] = len(var_map)
                flat_inst.extend([dst, var_map[var_name]])
            elif op == Op.STORE_VAR:
                var_name = inst[1]
                src = inst[2]
                if src in str_regs:
                    str_vars[var_name] = str_regs[src]
                else:
                    str_vars.pop(var_name, None)
                if var_name not in var_map:
                    var_map[var_name] = len(var_map)
                flat_inst.extend([var_map[var_name], src])
            elif op in (Op.ADD, Op.SUB, Op.MUL, Op.DIV, Op.MOD,
                        Op.CMP_EQ, Op.CMP_NE, Op.CMP_LT, Op.CMP_GT, Op.CMP_LE, Op.CMP_GE):
                flat_inst.extend([inst[1], inst[2], inst[3]])
            elif op == Op.JUMP:
                target = inst_to_flat.get(inst[1], inst[1])
                flat_inst.append(target)
            elif op == Op.JUMP_IF_FALSE:
                target = inst_to_flat.get(inst[2], inst[2])
                flat_inst.extend([inst[1], target])
            elif op == Op.PRINT:
                if inst[1] in str_regs:
                    flat_inst.extend([1, str_regs[inst[1]]])
                else:
                    flat_inst.extend([0, inst[1]])
            elif op == Op.EMIT:
                flat_inst.append(inst[1])
            elif op == Op.HALT:
                pass
            elif op == Op.GET_TIME:
                flat_inst.append(inst[1])
            elif op in (Op.SIN, Op.COS, Op.SQRT):
                flat_inst.extend([inst[1], inst[2]])
            elif op == Op.RND:
                flat_inst.append(inst[1])
            elif op == Op.CALL:
                # [19, func_id, arg_count, dst, arg0, ...]
                func_id = inst_to_flat.get(inst[2], inst[2]) if isinstance(inst[2], int) else get_str_idx(inst[2])
                args = inst[3] if len(inst) > 3 else []
                flat_inst.extend([func_id, len(args), inst[1]])
                flat_inst.extend(args)
            elif op == Op.RETURN:
                flat_inst.append(inst[1])
            elif op == Op.BUILD_LIST:
                # [28, cap_idx, dst, count, elem0_reg, elem1_reg...]
                elements = inst[2] if len(inst) > 2 else []
                cap_idx = get_num_idx(len(elements))
                flat_inst.extend([cap_idx, inst[1], len(elements)] + elements)
            elif op == Op.GET_INDEX:
                # [29, dst, arr_reg, idx_reg]
                flat_inst.extend([inst[1], inst[2], inst[3]])
            elif op == Op.SET_INDEX:
                # [30, arr_reg, idx_reg, val_reg]
                flat_inst.extend([inst[1], inst[2], inst[3]])

        return flat_inst, num_consts, str_consts

    def run_flat(self, flat_inst, num_consts, str_consts):
        """Runs pre-flattened bytecode directly on the C engine."""
        c_inst = (ctypes.c_int32 * len(flat_inst))(*flat_inst)
        c_nums = (ctypes.c_double * len(num_consts))(*num_consts) if num_consts else None
        c_strs = (ctypes.c_char_p * len(str_consts))(*[s.encode('utf-8') for s in str_consts]) if str_consts else None

        res = self.lib.run_bytecode(
            c_inst, len(flat_inst),
            c_nums, len(num_consts),
            c_strs, len(str_consts)
        )
        return int(res) if res.is_integer() else res

    def run(self, code_pkg):
        flat_inst, num_consts, str_consts = self.compile_payload(code_pkg)
        return self.run_flat(flat_inst, num_consts, str_consts)

    def run_foxc(self, foxc_path: str):
        """AOT Fast Path: Loads .foxc directly from disk and runs on foxvm.so without Python overhead."""
        flat_inst, num_consts, str_consts = deserialize_foxc(foxc_path)
        return self.run_flat(flat_inst, num_consts, str_consts)

    def compile_fox_file(self, fox_path: str, foxc_path: str = None) -> str:
        """Compiles a .fox source file to a binary AOT .foxc bytecode file."""
        if foxc_path is None:
            foxc_path = os.path.splitext(fox_path)[0] + ".foxc"
        with open(fox_path, "r", encoding="utf-8") as f:
            code = f.read()
        from engine.lexer import Lexer
        from engine.parser import Parser
        from engine.bytecode import BytecodeCompiler
        ast = Parser(Lexer(code).tokenize()).parse()
        pkg = BytecodeCompiler().compile(ast)
        flat_inst, num_consts, str_consts = self.compile_payload(pkg)
        serialize_foxc(foxc_path, flat_inst, num_consts, str_consts)
        return foxc_path

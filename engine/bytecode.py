"""
FoxVC Production Register-Based Bytecode VM & Compiler (v0.6)
Complete AST coverage:
- Functions (ActDef) with emit return signal & CallFrames
- Blueprints / Structs (MoldDef) & dynamic instantiation
- Error Trapping & Recovery (TrapStatement, GuardStatement)
- Game Tick Loops (PulseStatement), Count Loops (CycleStatement), While Loops (SpinStatement)
- Interactive Input (AskExpression) & Module Imports (FuseStatement)
- Branching (PickStatement: pick / alt / otherwise)
- Data Structures (ListLiteral, PackLiteral, IndexAccess, MemberAccess)
"""
import os
import time
from enum import Enum, auto
from typing import Any, List, Tuple, Dict, Optional

class Op(Enum):
    LOAD_CONST    = auto()   # (dest_reg, value)
    LOAD_VAR      = auto()   # (dest_reg, var_name)
    STORE_VAR     = auto()   # (var_name, src_reg)
    ADD           = auto()   # (dest_reg, src1, src2)
    SUB           = auto()   # (dest_reg, src1, src2)
    MUL           = auto()   # (dest_reg, src1, src2)
    DIV           = auto()   # (dest_reg, src1, src2)
    MOD           = auto()   # (dest_reg, src1, src2)
    CMP_EQ        = auto()   # (dest_reg, src1, src2)
    CMP_NE        = auto()   # (dest_reg, src1, src2)
    CMP_LT        = auto()   # (dest_reg, src1, src2)
    CMP_GT        = auto()   # (dest_reg, src1, src2)
    CMP_LE        = auto()   # (dest_reg, src1, src2)
    CMP_GE        = auto()   # (dest_reg, src1, src2)
    LOGIC_NOT     = auto()   # (dest_reg, src_reg)
    JUMP          = auto()   # (target_ip,)
    JUMP_IF_FALSE = auto()   # (cond_reg, target_ip)
    PRINT         = auto()   # (src_reg,)
    CALL          = auto()   # (dest_reg, func_name, [arg_regs])
    RETURN        = auto()   # (src_reg,)
    EMIT          = auto()   # (src_reg,)
    BUILD_LIST    = auto()   # (dest_reg, [elem_regs])
    BUILD_PACK    = auto()   # (dest_reg, [(k_reg, v_reg)])
    GET_INDEX     = auto()   # (dest_reg, obj_reg, idx_reg)
    SET_INDEX     = auto()   # (obj_reg, idx_reg, val_reg)
    GET_MEMBER    = auto()   # (dest_reg, obj_reg, member_name)
    SET_MEMBER    = auto()   # (obj_reg, member_name, val_reg)
    DEFINE_MOLD   = auto()   # (mold_name, src_pack_reg)
    GUARD         = auto()   # (cond_reg, line, col)
    SETUP_TRAP    = auto()   # (recover_ip,)
    POP_TRAP      = auto()   # ()
    ASK_INPUT     = auto()   # (dest_reg, prompt_reg)
    GET_TIME      = auto()   # (dest_reg,)
    FUSE_MODULE   = auto()   # (module_name,)
    HALT          = auto()   # ()
    SIN           = auto()   # (dest_reg, src_reg)
    COS           = auto()   # (dest_reg, src_reg)
    SQRT          = auto()   # (dest_reg, src_reg)
    RND           = auto()   # (dest_reg,)

class FunctionBlock:
    def __init__(self, name: str, params: List[str], instructions: List[Tuple]):
        self.name = name
        self.params = params
        self.instructions = instructions

def _extract_name(obj: Any) -> str:
    if isinstance(obj, str):
        return obj
    if hasattr(obj, "name") and isinstance(obj.name, str):
        return obj.name
    if hasattr(obj, "value") and isinstance(obj.value, str):
        return obj.value
    if hasattr(obj, "name"):
        return _extract_name(obj.name)
    return str(obj)

class BytecodeCompiler:
    def __init__(self):
        self.instructions: List[Tuple] = []
        self.functions: Dict[str, FunctionBlock] = {}
        self.next_reg = 0
        self.current_func: Optional[str] = None
        self.loop_stack: List[Dict[str, Any]] = []

    def alloc_reg(self) -> int:
        r = self.next_reg
        self.next_reg += 1
        return r

    def target_stream(self) -> List[Tuple]:
        return self.instructions if not self.current_func else self.functions[self.current_func].instructions

    def emit_op(self, op: Op, *args) -> int:
        target = self.target_stream()
        idx = len(target)
        target.append((op, *args))
        return idx

    def patch_op(self, idx: int, *args):
        target = self.target_stream()
        op = target[idx][0]
        target[idx] = (op, *args)

    def compile(self, ast_node) -> Tuple[List[Tuple], Dict[str, FunctionBlock]]:
        self.instructions = []
        self.line_map = {}
        self.functions = {}
        self.next_reg = 0
        self.current_func = None
        self.loop_stack = []

        nodes = getattr(ast_node, "statements", getattr(ast_node, "body", ast_node))
        if not isinstance(nodes, list):
            nodes = [nodes]

        for n in nodes:
            self.compile_node(n)
        self.emit_op(Op.HALT)
        return self.instructions, self.functions, self.line_map

    def compile_node(self, node) -> int:
        if node is None:
            return 0
        t = type(node).__name__

        # 1. EMIT STATEMENTS
        if t in ("EmitStmt", "EmitStatement"):
            expr = getattr(node, "value", getattr(node, "expression", None))
            val_reg = self.compile_node(expr)
            if self.current_func:
                self.emit_op(Op.RETURN, val_reg)
            else:
                self.emit_op(Op.EMIT, val_reg)
            return val_reg

        # 2. SAY STATEMENTS
        if t in ("SayStatement", "PrintStmt", "PrintStatement"):
            expr = getattr(node, "expression", getattr(node, "value", None))
            val_reg = self.compile_node(expr)
            self.emit_op(Op.PRINT, val_reg)
            return val_reg

        # 3. ASSIGNMENT & LOCK STATEMENTS
        if t in ("AssignmentStatement", "LockStatement"):
            expr = getattr(node, "expression", getattr(node, "value", None))
            val_reg = self.compile_node(expr)
            tgt = getattr(node, "target", getattr(node, "name", None))
            tgt_type = type(tgt).__name__

            if isinstance(tgt, str):
                self.emit_op(Op.STORE_VAR, tgt, val_reg)
            elif tgt_type == "Identifier":
                self.emit_op(Op.STORE_VAR, _extract_name(tgt), val_reg)
            elif tgt_type == "IndexAccess":
                obj_reg = self.compile_node(tgt.target)
                idx_reg = self.compile_node(tgt.index)
                self.emit_op(Op.SET_INDEX, obj_reg, idx_reg, val_reg)
            elif tgt_type == "MemberAccess":
                obj_reg = self.compile_node(tgt.obj)
                self.emit_op(Op.SET_MEMBER, obj_reg, _extract_name(tgt.member), val_reg)
            else:
                self.emit_op(Op.STORE_VAR, _extract_name(tgt), val_reg)
            return val_reg

        # 4. FUNCTIONS: ActDef
        if t == "ActDef":
            func_name = _extract_name(node.name)
            params = [_extract_name(p) for p in node.params]

            saved_reg = self.next_reg
            self.next_reg = 0
            self.functions[func_name] = FunctionBlock(func_name, params, [])
            old_func = self.current_func
            self.current_func = func_name

            body = node.body if isinstance(node.body, list) else [node.body]
            for stmt in body:
                self.compile_node(stmt)

            zero_reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, zero_reg, None)
            self.emit_op(Op.RETURN, zero_reg)

            self.current_func = old_func
            self.next_reg = saved_reg
            return 0

        # 5. MOLDS (Blueprints): MoldDef
        if t == "MoldDef":
            mold_name = _extract_name(node.name)
            field_regs = []
            for k, expr in node.fields.items():
                k_reg = self.alloc_reg()
                self.emit_op(Op.LOAD_CONST, k_reg, _extract_name(k))
                v_reg = self.compile_node(expr)
                field_regs.append((k_reg, v_reg))
            dest = self.alloc_reg()
            self.emit_op(Op.BUILD_PACK, dest, field_regs)
            self.emit_op(Op.DEFINE_MOLD, mold_name, dest)
            self.emit_op(Op.STORE_VAR, mold_name, dest)
            return dest

        # 6. FUNCTION & MOLD CALLS: CallExpression
        if t == "CallExpression":
            fn_name = _extract_name(node.function)
            dest_reg = self.alloc_reg()

            # Dedicated Native Timer Hook
            if fn_name == "time":
                self.emit_op(Op.GET_TIME, dest_reg)
                return dest_reg

            arg_regs = [self.compile_node(arg) for arg in node.arguments]
            self.emit_op(Op.CALL, dest_reg, fn_name, arg_regs)
            return dest_reg

        # 7. BRANCHING: PickStatement
        if t == "PickStatement":
            cond_reg = self.compile_node(node.condition)
            jump_false_idx = self.emit_op(Op.JUMP_IF_FALSE, cond_reg, -1)

            body = node.body if isinstance(node.body, list) else [node.body]
            for stmt in body:
                self.compile_node(stmt)

            jump_end_indices = []
            if node.alts or node.otherwise_body:
                jump_end_indices.append(self.emit_op(Op.JUMP, -1))

            self.patch_op(jump_false_idx, cond_reg, len(self.target_stream()))

            alts = node.alts if isinstance(node.alts, list) else []
            for alt in alts:
                alt_cond = alt[0] if isinstance(alt, tuple) else getattr(alt, "condition", None)
                alt_body_raw = alt[1] if isinstance(alt, tuple) else getattr(alt, "body", [])
                alt_cond_reg = self.compile_node(alt_cond)
                next_alt_jump = self.emit_op(Op.JUMP_IF_FALSE, alt_cond_reg, -1)

                alt_body = alt_body_raw if isinstance(alt_body_raw, list) else [alt_body_raw]
                for stmt in alt_body:
                    self.compile_node(stmt)

                jump_end_indices.append(self.emit_op(Op.JUMP, -1))
                self.patch_op(next_alt_jump, alt_cond_reg, len(self.target_stream()))

            if node.otherwise_body:
                other_body = node.otherwise_body if isinstance(node.otherwise_body, list) else [node.otherwise_body]
                for stmt in other_body:
                    self.compile_node(stmt)

            for j_idx in jump_end_indices:
                self.patch_op(j_idx, len(self.target_stream()))
            return 0

        # 8. SPIN LOOPS: SpinStatement
        if t == "SpinStatement":
            start_ip = len(self.target_stream())
            cond_reg = self.compile_node(node.condition)
            exit_jump = self.emit_op(Op.JUMP_IF_FALSE, cond_reg, -1)

            self.loop_stack.append({"start": start_ip, "halts": []})

            body = node.body if isinstance(node.body, list) else [node.body]
            for stmt in body:
                self.compile_node(stmt)

            self.emit_op(Op.JUMP, start_ip)
            end_ip = len(self.target_stream())
            self.patch_op(exit_jump, cond_reg, end_ip)

            loop_ctx = self.loop_stack.pop()
            for h_idx in loop_ctx["halts"]:
                self.patch_op(h_idx, end_ip)
            return 0

        # 9. CYCLE LOOPS: CycleStatement
        if t == "CycleStatement":
            var_name = _extract_name(node.var_name)
            count_reg = self.compile_node(node.count_expr)
            iter_reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, iter_reg, 0)
            self.emit_op(Op.STORE_VAR, var_name, iter_reg)

            start_ip = len(self.target_stream())
            cmp_reg = self.alloc_reg()
            self.emit_op(Op.CMP_LT, cmp_reg, iter_reg, count_reg)
            exit_jump = self.emit_op(Op.JUMP_IF_FALSE, cmp_reg, -1)

            self.loop_stack.append({"start": start_ip, "halts": []})

            body = node.body if isinstance(node.body, list) else [node.body]
            for stmt in body:
                self.compile_node(stmt)

            one_reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, one_reg, 1)
            self.emit_op(Op.ADD, iter_reg, iter_reg, one_reg)
            self.emit_op(Op.STORE_VAR, var_name, iter_reg)

            self.emit_op(Op.JUMP, start_ip)
            end_ip = len(self.target_stream())
            self.patch_op(exit_jump, cmp_reg, end_ip)

            loop_ctx = self.loop_stack.pop()
            for h_idx in loop_ctx["halts"]:
                self.patch_op(h_idx, end_ip)
            return 0

        # 10. PULSE GAME LOOP: PulseStatement (delta_var, body)
        # 10. PULSE GAME LOOP: PulseStatement (delta_var, body)
        if t == "PulseStatement":
            delta_var = _extract_name(node.delta_var)
            prev_t_reg = self.alloc_reg()
            curr_t_reg = self.alloc_reg()
            dt_reg = self.alloc_reg()
            zero_r = self.alloc_reg()

            self.emit_op(Op.GET_TIME, prev_t_reg)
            start_ip = len(self.target_stream())
            self.emit_op(Op.GET_TIME, curr_t_reg)
            self.emit_op(Op.SUB, dt_reg, curr_t_reg, prev_t_reg)

            # Update prev_t = curr_t cleanly (3-register ADD: dest, src1, src2)
            self.emit_op(Op.LOAD_CONST, zero_r, 0.0)
            self.emit_op(Op.ADD, prev_t_reg, curr_t_reg, zero_r)
            self.emit_op(Op.STORE_VAR, delta_var, dt_reg)

            self.loop_stack.append({"start": start_ip, "halts": []})

            body = node.body if isinstance(node.body, list) else [node.body]
            for stmt in body:
                self.compile_node(stmt)

            self.emit_op(Op.JUMP, start_ip)
            end_ip = len(self.target_stream())
            loop_ctx = self.loop_stack.pop()
            for h_idx in loop_ctx["halts"]:
                self.patch_op(h_idx, end_ip)
            return 0
        # 11. LOOP CONTROL: HaltStmt & SkipStmt
        if t == "HaltStmt":
            if self.loop_stack:
                h_idx = self.emit_op(Op.JUMP, -1)
                self.loop_stack[-1]["halts"].append(h_idx)
            else:
                self.emit_op(Op.HALT)
            return 0

        if t == "SkipStmt":
            if self.loop_stack:
                self.emit_op(Op.JUMP, self.loop_stack[-1]["start"])
            return 0

        # 12. SHIFT, GUARD & TRAP STATEMENTS
        if t == "ShiftStatement":
            return self.compile_node(getattr(node, "target_stmt", None))

        if t == "GuardStatement":
            cond_reg = self.compile_node(node.condition)
            line = getattr(node, "line", None)
            col = getattr(node, "column", None)
            self.emit_op(Op.GUARD, cond_reg, line, col)
            return 0

        if t == "TrapStatement":
            setup_idx = self.emit_op(Op.SETUP_TRAP, -1)
            try_body = node.try_body if isinstance(node.try_body, list) else [node.try_body]
            for stmt in try_body:
                self.compile_node(stmt)
            self.emit_op(Op.POP_TRAP)
            jump_over_catch = self.emit_op(Op.JUMP, -1)

            recover_ip = len(self.target_stream())
            self.patch_op(setup_idx, recover_ip)

            catch_body = getattr(node, "catch_body", [])
            if catch_body:
                catch_list = catch_body if isinstance(catch_body, list) else [catch_body]
                for stmt in catch_list:
                    self.compile_node(stmt)

            end_ip = len(self.target_stream())
            self.patch_op(jump_over_catch, end_ip)
            return 0

        # 13. ASK EXPRESSION & FUSE STATEMENT
        if t == "AskExpression":
            prompt_reg = self.compile_node(node.prompt)
            dest = self.alloc_reg()
            self.emit_op(Op.ASK_INPUT, dest, prompt_reg)
            return dest

        if t == "FuseStatement":
            mod_name = _extract_name(node.module_name)
            self.emit_op(Op.FUSE_MODULE, mod_name)
            return 0

        # 14. DATA STRUCTURES: ListLiteral, PackLiteral, IndexAccess, MemberAccess
        if t == "ListLiteral":
            elem_regs = [self.compile_node(el) for el in node.elements]
            dest = self.alloc_reg()
            self.emit_op(Op.BUILD_LIST, dest, elem_regs)
            return dest

        if t == "PackLiteral":
            entry_regs = []
            for k, v in node.entries.items():
                k_reg = self.alloc_reg()
                self.emit_op(Op.LOAD_CONST, k_reg, _extract_name(k))
                v_reg = self.compile_node(v)
                entry_regs.append((k_reg, v_reg))
            dest = self.alloc_reg()
            self.emit_op(Op.BUILD_PACK, dest, entry_regs)
            return dest

        if t == "IndexAccess":
            obj_reg = self.compile_node(node.target)
            idx_reg = self.compile_node(node.index)
            dest = self.alloc_reg()
            self.emit_op(Op.GET_INDEX, dest, obj_reg, idx_reg)
            return dest

        if t == "MemberAccess":
            obj_reg = self.compile_node(node.obj)
            dest = self.alloc_reg()
            self.emit_op(Op.GET_MEMBER, dest, obj_reg, _extract_name(node.member))
            return dest

        # 15. BINARY & UNARY OPERATIONS
        if t == "BinaryOp":
            l_reg = self.compile_node(node.left)
            r_reg = self.compile_node(node.right)
            dest = self.alloc_reg()
            raw_op = node.op.value if hasattr(node.op, "value") else str(node.op)

            op_table = {
                "+": Op.ADD, "PLUS": Op.ADD,
                "-": Op.SUB, "MINUS": Op.SUB,
                "*": Op.MUL, "STAR": Op.MUL,
                "/": Op.DIV, "SLASH": Op.DIV,
                "%": Op.MOD, "PERCENT": Op.MOD,
                "==": Op.CMP_EQ, "EQ": Op.CMP_EQ,
                "!=": Op.CMP_NE, "NE": Op.CMP_NE,
                "<": Op.CMP_LT, "LT": Op.CMP_LT,
                ">": Op.CMP_GT, "GT": Op.CMP_GT,
                "<=": Op.CMP_LE, "LE": Op.CMP_LE,
                ">=": Op.CMP_GE, "GE": Op.CMP_GE,
                "also": Op.MUL, "either": Op.ADD
            }
            self.emit_op(op_table.get(raw_op, Op.ADD), dest, l_reg, r_reg)
            return dest

        if t == "UnaryOp":
            expr_reg = self.compile_node(node.operand)
            dest = self.alloc_reg()
            raw_op = node.op.value if hasattr(node.op, "value") else str(node.op)
            if raw_op in ("not", "deny", "!"):
                self.emit_op(Op.LOGIC_NOT, dest, expr_reg)
            elif raw_op == "-":
                zero_reg = self.alloc_reg()
                self.emit_op(Op.LOAD_CONST, zero_reg, 0)
                self.emit_op(Op.SUB, dest, zero_reg, expr_reg)
            return dest

        # 16. LITERALS & IDENTIFIERS
        if t == "Identifier":
            reg = self.alloc_reg()
            self.emit_op(Op.LOAD_VAR, reg, _extract_name(node.name))
            return reg

        if t == "NumberLiteral":
            reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, reg, node.value)
            return reg

        if t == "StringLiteral":
            reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, reg, node.value)
            return reg

        if t == "BooleanLiteral":
            reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, reg, bool(node.value))
            return reg

        if t == "BlankLiteral":
            reg = self.alloc_reg()
            self.emit_op(Op.LOAD_CONST, reg, None)
            return reg

        reg = self.alloc_reg()
        self.emit_op(Op.LOAD_CONST, reg, getattr(node, "value", None))
        return reg

class CallFrame:
    def __init__(self, func_name: str, return_ip: int, dest_reg: int, caller_regs: List[Any]):
        self.func_name = func_name
        self.return_ip = return_ip
        self.dest_reg = dest_reg
        self.caller_regs = caller_regs
        self.locals: Dict[str, Any] = {}

class FoxVM:
    def __init__(self, num_registers: int = 256):
        self.registers = [None] * num_registers
        self.globals: Dict[str, Any] = {}
        self.molds: Dict[str, Dict[str, Any]] = {}
        self.call_stack: List[CallFrame] = []
        self.trap_stack: List[Tuple] = []
        self.functions: Dict[str, FunctionBlock] = {}
        self.ip = 0

    def run(self, code_package: Any) -> Any:
        if isinstance(code_package, tuple):
            code, self.functions = code_package
        else:
            code, self.functions = code_package, {}

        self.ip = 0
        self.call_stack = []
        self.trap_stack = []
        regs = self.registers
        last_emitted = None
        active_code = code

        while self.ip < len(active_code):
            inst = active_code[self.ip]
            op = inst[0]

            try:
                if op == Op.LOAD_CONST:
                    regs[inst[1]] = inst[2]

                elif op == Op.LOAD_VAR:
                    var_name = inst[2]
                    if self.call_stack and var_name in self.call_stack[-1].locals:
                        regs[inst[1]] = self.call_stack[-1].locals[var_name]
                    elif var_name in self.globals:
                        regs[inst[1]] = self.globals[var_name]
                    else:
                        raise RuntimeError(f"Undefined variable '{var_name}'")

                elif op == Op.STORE_VAR:
                    var_name = inst[1]
                    val = regs[inst[2]]
                    if self.call_stack:
                        self.call_stack[-1].locals[var_name] = val
                    else:
                        self.globals[var_name] = val

                elif op == Op.DEFINE_MOLD:
                    mold_name = inst[1]
                    template_dict = dict(regs[inst[2]])
                    self.molds[mold_name] = template_dict
                    self.globals[mold_name] = template_dict

                elif op == Op.ADD:
                    regs[inst[1]] = regs[inst[2]] + regs[inst[3]]
                elif op == Op.SUB:
                    regs[inst[1]] = regs[inst[2]] - regs[inst[3]]
                elif op == Op.MUL:
                    regs[inst[1]] = regs[inst[2]] * regs[inst[3]]
                elif op == Op.DIV:
                    regs[inst[1]] = regs[inst[2]] / regs[inst[3]]
                elif op == Op.MOD:
                    regs[inst[1]] = regs[inst[2]] % regs[inst[3]]

                elif op == Op.CMP_EQ:
                    regs[inst[1]] = (regs[inst[2]] == regs[inst[3]])
                elif op == Op.CMP_NE:
                    regs[inst[1]] = (regs[inst[2]] != regs[inst[3]])
                elif op == Op.CMP_LT:
                    regs[inst[1]] = (regs[inst[2]] < regs[inst[3]])
                elif op == Op.CMP_GT:
                    regs[inst[1]] = (regs[inst[2]] > regs[inst[3]])
                elif op == Op.CMP_LE:
                    regs[inst[1]] = (regs[inst[2]] <= regs[inst[3]])
                elif op == Op.CMP_GE:
                    regs[inst[1]] = (regs[inst[2]] >= regs[inst[3]])
                elif op == Op.LOGIC_NOT:
                    regs[inst[1]] = not regs[inst[2]]

                elif op == Op.JUMP:
                    self.ip = inst[1]
                    continue
                elif op == Op.JUMP_IF_FALSE:
                    if not regs[inst[1]]:
                        self.ip = inst[2]
                        continue

                elif op == Op.PRINT:
                    val = regs[inst[1]]
                    if isinstance(val, bool):
                        print("aye" if val else "nay")
                    else:
                        print(val)

                elif op == Op.BUILD_LIST:
                    regs[inst[1]] = [regs[r] for r in inst[2]]

                elif op == Op.BUILD_PACK:
                    regs[inst[1]] = {regs[k]: regs[v] for k, v in inst[2]}

                elif op == Op.GET_INDEX:
                    regs[inst[1]] = regs[inst[2]][regs[inst[3]]]

                elif op == Op.SET_INDEX:
                    regs[inst[1]][regs[inst[2]]] = regs[inst[3]]

                elif op == Op.GET_MEMBER:
                    obj = regs[inst[2]]
                    member = inst[3]
                    if isinstance(obj, dict):
                        if member not in obj:
                            raise RuntimeError(f"Missing field '{member}' on mold/pack")
                        regs[inst[1]] = obj[member]
                    else:
                        regs[inst[1]] = getattr(obj, member)

                elif op == Op.SET_MEMBER:
                    obj = regs[inst[1]]
                    member = inst[2]
                    val = regs[inst[3]]
                    if isinstance(obj, dict):
                        obj[member] = val
                    else:
                        setattr(obj, member, val)

                elif op == Op.CALL:
                    dest_reg, fn_name, arg_regs = inst[1], inst[2], inst[3]
                    # 1. Check if it is a Mold blueprint instantiation (e.g. Player())
                    if fn_name in self.molds:
                        instance = dict(self.molds[fn_name])
                        # Optional positional field overrides if arguments were passed
                        if arg_regs:
                            keys = list(instance.keys())
                            for i_arg, a_reg in enumerate(arg_regs):
                                if i_arg < len(keys):
                                    instance[keys[i_arg]] = regs[a_reg]
                        regs[dest_reg] = instance
                    elif fn_name in self.globals and isinstance(self.globals[fn_name], dict):
                        regs[dest_reg] = dict(self.globals[fn_name])
                    # 2. Check if it is an act function
                    elif fn_name in self.functions:
                        fn_block = self.functions[fn_name]
                        frame = CallFrame(fn_name, self.ip + 1, dest_reg, list(regs))
                        for p_name, a_reg in zip(fn_block.params, arg_regs):
                            frame.locals[p_name] = regs[a_reg]
                        self.call_stack.append(frame)

                        regs = [None] * len(regs)
                        self.registers = regs
                        active_code = fn_block.instructions
                        self.ip = 0
                        continue
                    else:
                        raise RuntimeError(f"Undefined function or mold '{fn_name}' in FoxVM")

                elif op == Op.RETURN:
                    ret_val = regs[inst[1]]
                    if self.call_stack:
                        frame = self.call_stack.pop()
                        regs = frame.caller_regs
                        self.registers = regs
                        regs[frame.dest_reg] = ret_val
                        self.ip = frame.return_ip
                        # GC sweep: clear lingering local registers
                        self.registers = regs
                        active_code = code if not self.call_stack else self.functions[self.call_stack[-1].func_name].instructions
                        continue
                    else:
                        return ret_val

                elif op == Op.GUARD:
                    cond_val = regs[inst[1]]
                    if not bool(cond_val):
                        line, col = inst[2], inst[3]
                        pos_str = f" [Line {line}, Col {col}]" if line else ""
                        raise RuntimeError(f"Guard condition failed{pos_str}")

                elif op == Op.SETUP_TRAP:
                    # Push (recover_ip, call_stack_depth, active_code_ref, registers_snapshot)
                    self.trap_stack.append((inst[1], len(self.call_stack), active_code, list(regs)))

                elif op == Op.POP_TRAP:
                    if self.trap_stack:
                        self.trap_stack.pop()

                elif op == Op.ASK_INPUT:
                    prompt_val = regs[inst[2]]
                    user_in = input("" if prompt_val is None else str(prompt_val))
                    # Auto-convert numeric strings if appropriate, else keep string
                    try:
                        regs[inst[1]] = int(user_in)
                    except ValueError:
                        try:
                            regs[inst[1]] = float(user_in)
                        except ValueError:
                            regs[inst[1]] = user_in

                elif op == Op.GET_TIME:
                    regs[inst[1]] = time.time()

                elif op == Op.FUSE_MODULE:
                    mod_name = inst[1]
                    mod_file = mod_name if mod_name.endswith(".fox") else f"{mod_name}.fox"
                    if os.path.exists(mod_file):
                        from engine.lexer import Lexer
                        from engine.parser import Parser
                        with open(mod_file, "r", encoding="utf-8") as mf:
                            mod_src = mf.read()
                        mod_ast = Parser(Lexer(mod_src).tokenize(), source=mod_src).parse()
                        sub_comp = BytecodeCompiler()
                        sub_code, sub_funcs = sub_comp.compile(mod_ast)
                        self.functions.update(sub_funcs)
                        sub_vm = FoxVM()
                        sub_vm.functions = self.functions
                        sub_vm.globals = self.globals
                        sub_vm.molds = self.molds
                        sub_vm.run((sub_code, self.functions))

                elif op == Op.EMIT:
                    last_emitted = regs[inst[1]]

                elif op == Op.HALT:
                    break

            except Exception as err:
                if self.trap_stack:
                    recover_ip, saved_depth, saved_code, saved_regs = self.trap_stack.pop()
                    while len(self.call_stack) > saved_depth:
                        self.call_stack.pop()
                    active_code = saved_code
                    # Restore caller registers if we unwound from inside an act call
                    for idx_r in range(min(len(regs), len(saved_regs))):
                        if regs[idx_r] is None:
                            regs[idx_r] = saved_regs[idx_r]
                    self.globals["_last_error"] = str(err)
                    self.ip = recover_ip
                    continue
                else:
                    raise

            self.ip += 1

        return last_emitted


    def compile_act_def(self, node):
        skip_jump = self.emit_op(Op.JUMP, 0)
        func_start_ip = len(self.instructions)
        params = getattr(node, "params", [])
        self.functions[node.name] = {
            "addr": func_start_ip,
            "params": params
        }
        old_locals = self.local_vars.copy()
        self.local_vars = {p: i for i, p in enumerate(params)}
        
        body = getattr(node, "body", [])
        if not isinstance(body, list):
            body = [body]
        for stmt in body:
            self.compile_node(stmt)
            
        nil_reg = self.alloc_reg()
        self.emit_op(Op.LOAD_CONST, nil_reg, self.add_const(0.0))
        self.emit_op(Op.RETURN, nil_reg)
        self.local_vars = old_locals
        self.patch_op(skip_jump, len(self.instructions))
        return None

    def compile_call(self, node):
        callee = getattr(node, "callee", getattr(node, "name", None))
        args = getattr(node, "args", [])
        arg_regs = [self.compile_node(a) for a in args]
        res_reg = self.alloc_reg()
        
        # Generic FoxVC Primitives (No hardcoded game functions)
        if callee == "bind":
            # bind("symbol_name", arg1, arg2...)
            fn_name_node = args[0]
            fn_name = getattr(fn_name_node, "value", "unknown")
            str_idx = self.add_string(str(fn_name))
            arg_regs = [self.compile_node(a) for a in args[1:]]
            res_reg = self.alloc_reg()
            self.emit_op(Op.BIND_CALL, str_idx, len(arg_regs), res_reg, *arg_regs)
            return res_reg
        elif callee == "pack":
            # pack(size)
            cap_reg = self.compile_node(args[0])
            res_reg = self.alloc_reg()
            self.emit_op(Op.PACK_NEW, cap_reg, res_reg)
            return res_reg
        elif callee == "pack_get":
            # pack_get(pack_id, index)
            p_reg = self.compile_node(args[0])
            i_reg = self.compile_node(args[1])
            res_reg = self.alloc_reg()
            self.emit_op(Op.PACK_GET, p_reg, i_reg, res_reg)
            return res_reg
        elif callee == "pack_set":
            # pack_set(pack_id, index, value)
            p_reg = self.compile_node(args[0])
            i_reg = self.compile_node(args[1])
            v_reg = self.compile_node(args[2])
            self.emit_op(Op.PACK_SET, p_reg, i_reg, v_reg)
            return v_reg

        if callee in self.functions:
            f_meta = self.functions[callee]
            self.emit_op(Op.CALL, f_meta["addr"], len(arg_regs), res_reg)
        else:
            # Fallback or built-in handling
            pass
        return res_reg

    def add_string(self, s):
        if s not in self.str_constants:
            self.str_constants.append(s)
        return self.str_constants.index(s)

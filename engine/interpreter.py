"""
FoxVC Interpreter Engine (v0.5.2x)
Complete 25-keyword runtime with Native Lists, Indexing, and Real Pulse Loops.
"""

from typing import Any, Dict, List, Optional
import os
import time
from .shelf import get_standard_shelf


class RuntimeError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0, file: Optional[str] = None):
        super().__init__(f"Runtime Error [{file or 'unknown'}] [Line {line}, Col {column}]: {message}")
        self.message = message
        self.line = line
        self.column = column
        self.file = file


class EmitSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


class HaltSignal(Exception):
    pass


class SkipSignal(Exception):
    pass


class FoxPack:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return f"pack {self._data}"


def get_foxvc_type(val: Any) -> str:
    if val is None:
        return "blank"
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, (int, float)):
        return "num"
    if isinstance(val, str):
        return "text"
    if isinstance(val, list):
        return "list"
    if isinstance(val, FoxPack):
        return "pack"
    return type(val).__name__


def is_foxvc_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


class Interpreter:
    def __init__(self):
        self.shelf = get_standard_shelf()
        self.variables: Dict[str, Any] = dict(self.shelf)
        self.locked_variables: set = set()
        self.functions: Dict[str, Any] = {}
        self.molds: Dict[str, Any] = {}
        self.active_file: Optional[str] = "main.fox"
        self.output_buffer: List[str] = []

    def reset(self):
        self.variables = dict(self.shelf)
        self.locked_variables.clear()
        self.functions.clear()
        self.molds.clear()
        self.output_buffer.clear()

    def execute(self, program_ast: Any):
        if not program_ast:
            return None
        self.active_file = getattr(program_ast, "file", self.active_file)
        statements = getattr(program_ast, "statements", [])
        for statement in statements:
            self._execute_statement(statement)

    def _execute_statement(self, stmt: Any):
        if stmt is None:
            return None

        node_name = type(stmt).__name__

        if node_name == "ActDef":
            self.functions[stmt.name] = stmt
            return None

        if node_name == "MoldDef":
            self.molds[stmt.name] = stmt
            return None

        if node_name == "EmitStmt":
            val = self._evaluate(stmt.value) if getattr(stmt, "value", None) else None
            raise EmitSignal(val)

        if node_name == "HaltStmt":
            raise HaltSignal()

        if node_name == "SkipStmt":
            raise SkipSignal()

        if node_name == "LockStatement":
            val = self._evaluate(stmt.expression)
            self.variables[stmt.name] = val
            self.locked_variables.add(stmt.name)
            return val

        if node_name == "ShiftStatement":
            return self._execute_statement(stmt.target_stmt)

        if node_name == "GuardStatement":
            cond = self._evaluate(stmt.condition)
            if not bool(cond):
                raise RuntimeError("Guard condition failed", stmt.line, stmt.column, self.active_file)
            return None

        if node_name == "TrapStatement":
            try:
                for s in stmt.try_body:
                    self._execute_statement(s)
            except Exception:
                if stmt.catch_body:
                    for s in stmt.catch_body:
                        self._execute_statement(s)
            return None

        if node_name == "FuseStatement":
            mod_path = f"{stmt.module_name}.fox"
            if os.path.exists(mod_path):
                from .lexer import Lexer
                from .parser import Parser
                with open(mod_path, "r", encoding="utf-8") as f:
                    content = f.read()
                sub_ast = Parser(Lexer(content, mod_path).tokenize(), mod_path).parse()
                self.execute(sub_ast)
            return None

        if node_name == "CycleStatement":
            count = self._evaluate(stmt.count_expr)
            iterable = range(int(count)) if isinstance(count, (int, float)) else count
            for item in iterable:
                self.variables[stmt.var_name] = item
                try:
                    for s in stmt.body:
                        self._execute_statement(s)
                except HaltSignal:
                    break
                except SkipSignal:
                    continue
            return None

        if node_name == "PickStatement":
            condition = self._evaluate(stmt.condition)
            if bool(condition):
                for s in stmt.body:
                    self._execute_statement(s)
                return None
            
            for alt_cond, alt_body in getattr(stmt, "alts", []):
                if bool(self._evaluate(alt_cond)):
                    for s in alt_body:
                        self._execute_statement(s)
                    return None

            if stmt.otherwise_body:
                for s in stmt.otherwise_body:
                    self._execute_statement(s)
            return None

        # Continuous Heartbeat Pulse
        if node_name == "PulseStatement":
            last_time = time.time()
            try:
                while True:
                    current_time = time.time()
                    dt = round(current_time - last_time, 4)
                    if dt == 0:
                        dt = 0.001
                    last_time = current_time
                    self.variables[stmt.delta_var] = dt
                    try:
                        for s in stmt.body:
                            self._execute_statement(s)
                    except HaltSignal:
                        break
                    except SkipSignal:
                        continue
                    time.sleep(0.016)
            except KeyboardInterrupt:
                pass
            return None

        if node_name == "SpinStatement":
            while bool(self._evaluate(stmt.condition)):
                try:
                    for s in stmt.body:
                        self._execute_statement(s)
                except HaltSignal:
                    break
                except SkipSignal:
                    continue
            return None

        if node_name == "AssignmentStatement":
            val = self._evaluate(stmt.expression)
            target = stmt.target
            target_type = type(target).__name__

            if target_type == "Identifier":
                if target.name in self.locked_variables:
                    raise RuntimeError(f"Cannot mutate locked variable '{target.name}'", stmt.line, stmt.column, self.active_file)
                self.variables[target.name] = val
                return val

            if target_type == "MemberAccess":
                obj = self._evaluate(target.obj)
                if isinstance(obj, FoxPack):
                    obj[target.member] = val
                    return val
                raise RuntimeError(f"Cannot set property '{target.member}' on type '{get_foxvc_type(obj)}'", stmt.line, stmt.column, self.active_file)

            if target_type == "IndexAccess":
                container = self._evaluate(target.target)
                idx = self._evaluate(target.index)
                if isinstance(container, list):
                    idx_int = int(idx)
                    if 0 <= idx_int < len(container):
                        container[idx_int] = val
                        return val
                    raise RuntimeError(f"Index out of bounds: {idx_int}", stmt.line, stmt.column, self.active_file)
                if isinstance(container, FoxPack):
                    container[str(idx)] = val
                    return val
                raise RuntimeError(f"Cannot assign by index to type '{get_foxvc_type(container)}'", stmt.line, stmt.column, self.active_file)

            raise RuntimeError("Invalid assignment target", stmt.line, stmt.column, self.active_file)

        if node_name == "SayStatement":
            val = self._evaluate(stmt.expression)
            out_str = str(val) if val is not None else "blank"
            self.output_buffer.append(out_str)
            print(out_str)
            return None

        return self._evaluate(stmt)

    def _evaluate(self, node: Any) -> Any:
        if node is None:
            return None

        node_type = type(node).__name__

        if node_type == "NumberLiteral":
            return node.value
        if node_type == "StringLiteral":
            return str(node.value)
        if node_type == "BooleanLiteral":
            return bool(node.value)
        if node_type == "BlankLiteral":
            return None

        if node_type == "ListLiteral":
            return [self._evaluate(elem) for elem in node.elements]

        if node_type == "IndexAccess":
            target = self._evaluate(node.target)
            idx = self._evaluate(node.index)
            if isinstance(target, (list, str)):
                if isinstance(idx, (int, float)):
                    idx_int = int(idx)
                    if 0 <= idx_int < len(target):
                        return target[idx_int]
                    raise RuntimeError(f"Index out of bounds: {idx_int} (length {len(target)})", node.line, node.column, self.active_file)
                raise RuntimeError(f"Index must be a number, got '{get_foxvc_type(idx)}'", node.line, node.column, self.active_file)
            if isinstance(target, FoxPack):
                return target._data.get(str(idx))
            raise RuntimeError(f"Cannot index into type '{get_foxvc_type(target)}'", node.line, node.column, self.active_file)

        if node_type == "AskExpression":
            prompt = str(self._evaluate(node.prompt)) if getattr(node, "prompt", None) else ""
            try:
                res = input(prompt)
                try:
                    return float(res) if "." in res else int(res)
                except ValueError:
                    return res
            except (EOFError, KeyboardInterrupt):
                return ""

        if node_type == "PackLiteral":
            pack_dict = {}
            for k, expr in node.entries.items():
                pack_dict[k] = self._evaluate(expr)
            return FoxPack(pack_dict)

        if node_type == "MemberAccess":
            target = self._evaluate(node.obj)
            if isinstance(target, FoxPack):
                if node.member in target._data:
                    return target[node.member]
                raise RuntimeError(f"Pack has no property '{node.member}'", node.line, node.column, self.active_file)
            raise RuntimeError(f"Cannot access property on type '{get_foxvc_type(target)}'", node.line, node.column, self.active_file)

        if node_type == "Identifier":
            name = node.name
            if name in self.variables:
                return self.variables[name]
            raise RuntimeError(f"Undefined variable '{name}'", getattr(node, "line", 0), getattr(node, "column", 0), self.active_file)

        if node_type == "CallExpression":
            fn_name = node.function
            evaluated_args = [self._evaluate(a) for a in node.arguments]

            if fn_name in self.functions:
                fn = self.functions[fn_name]
                if len(evaluated_args) != len(fn.params):
                    raise RuntimeError(f"Act '{fn_name}' expects {len(fn.params)} arguments, got {len(evaluated_args)}", getattr(node, "line", 0), getattr(node, "column", 0), self.active_file)

                saved_vars = dict(self.variables)
                for param, val in zip(fn.params, evaluated_args):
                    self.variables[param] = val

                return_val = None
                try:
                    for s in fn.body:
                        self._execute_statement(s)
                except EmitSignal as sig:
                    return_val = sig.value
                finally:
                    self.variables = saved_vars
                return return_val

            if fn_name in self.molds:
                mold = self.molds[fn_name]
                inst_data = {}
                for k, expr in mold.fields.items():
                    inst_data[k] = self._evaluate(expr)
                return FoxPack(inst_data)

            if fn_name in self.variables and callable(self.variables[fn_name]):
                native_fn = self.variables[fn_name]
                try:
                    return native_fn(*evaluated_args)
                except Exception as e:
                    raise RuntimeError(f"Shelf call '{fn_name}' failed: {e}", getattr(node, "line", 0), getattr(node, "column", 0), self.active_file)

            raise RuntimeError(f"Undefined act or shelf function '{fn_name}'", getattr(node, "line", 0), getattr(node, "column", 0), self.active_file)

        if node_type == "BinaryOp":
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            op = node.op

            if op == "+":
                if isinstance(left, str) or isinstance(right, str):
                    def _fmt(val):
                        if isinstance(val, float) and val.is_integer():
                            return str(int(val))
                        return str(val) if val is not None else "blank"
                    return _fmt(left) + _fmt(right)
                if is_foxvc_number(left) and is_foxvc_number(right):
                    return left + right
                raise RuntimeError(f"Cannot add types '{get_foxvc_type(left)}' and '{get_foxvc_type(right)}'", node.line, node.column, self.active_file)

            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise RuntimeError("Division by zero", node.line, node.column, self.active_file)
                return left / right
            if op == "%":
                return left % right

            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right

            if op == "also":
                return bool(left and right)
            if op == "either":
                return bool(left or right)

        if node_type == "UnaryOp":
            operand = self._evaluate(node.operand)
            if node.op == "-":
                return -operand
            if node.op == "deny":
                return not bool(operand)

        raise RuntimeError(f"Cannot evaluate AST node '{node_type}'", getattr(node, "line", 0), getattr(node, "column", 0), self.active_file)

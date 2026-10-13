"""
FoxVC Parser Engine (v0.5.2x - Robust Multi-Line & Deep Indexing Edition)
"""

from typing import List, Optional, Any
from .lexer import Token, TokenType


class ASTNode:
    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column


class Program(ASTNode):
    def __init__(self, statements: List[ASTNode], file: str = "main.fox"):
        super().__init__(1, 1)
        self.statements = statements
        self.file = file


class NumberLiteral(ASTNode):
    def __init__(self, value: Any, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value


class StringLiteral(ASTNode):
    def __init__(self, value: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value


class BooleanLiteral(ASTNode):
    def __init__(self, value: bool, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value


class BlankLiteral(ASTNode):
    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(line, column)


class AskExpression(ASTNode):
    def __init__(self, prompt: Optional[ASTNode] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.prompt = prompt


class Identifier(ASTNode):
    def __init__(self, name: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name


class ListLiteral(ASTNode):
    def __init__(self, elements: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.elements = elements


class IndexAccess(ASTNode):
    def __init__(self, target: ASTNode, index: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.target = target
        self.index = index


class PackLiteral(ASTNode):
    def __init__(self, entries: dict, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.entries = entries


class MemberAccess(ASTNode):
    def __init__(self, obj: ASTNode, member: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.obj = obj
        self.member = member


class BinaryOp(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right


class UnaryOp(ASTNode):
    def __init__(self, op: str, operand: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.op = op
        self.operand = operand


class CallExpression(ASTNode):
    def __init__(self, function: str, arguments: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.function = function
        self.arguments = arguments


class AssignmentStatement(ASTNode):
    def __init__(self, target: ASTNode, expression: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.target = target
        self.expression = expression


class LockStatement(ASTNode):
    def __init__(self, name: str, expression: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
        self.expression = expression


class ShiftStatement(ASTNode):
    def __init__(self, target_stmt: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.target_stmt = target_stmt


class SayStatement(ASTNode):
    def __init__(self, expression: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.expression = expression


class EmitStmt(ASTNode):
    def __init__(self, value: Optional[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.value = value


class ActDef(ASTNode):
    def __init__(self, name: str, params: List[str], body: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
        self.params = params
        self.body = body


class MoldDef(ASTNode):
    def __init__(self, name: str, fields: dict, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.name = name
        self.fields = fields


class PickStatement(ASTNode):
    def __init__(self, condition: ASTNode, body: List[ASTNode], alts: List[Any], otherwise_body: Optional[List[ASTNode]] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body
        self.alts = alts
        self.otherwise_body = otherwise_body


class PulseStatement(ASTNode):
    def __init__(self, delta_var: str, body: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.delta_var = delta_var
        self.body = body


class SpinStatement(ASTNode):
    def __init__(self, condition: ASTNode, body: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body


class CycleStatement(ASTNode):
    def __init__(self, var_name: str, count_expr: ASTNode, body: List[ASTNode], line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.var_name = var_name
        self.count_expr = count_expr
        self.body = body


class GuardStatement(ASTNode):
    def __init__(self, condition: ASTNode, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.condition = condition


class TrapStatement(ASTNode):
    def __init__(self, try_body: List[ASTNode], catch_body: Optional[List[ASTNode]] = None, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.try_body = try_body
        self.catch_body = catch_body


class FuseStatement(ASTNode):
    def __init__(self, module_name: str, line: int = 0, column: int = 0):
        super().__init__(line, column)
        self.module_name = module_name


class HaltStmt(ASTNode):
    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(line, column)


class SkipStmt(ASTNode):
    def __init__(self, line: int = 0, column: int = 0):
        super().__init__(line, column)


class ParserError(Exception):
    SOURCE_LINES = []

    @classmethod
    def set_source(cls, source: str):
        cls.SOURCE_LINES = source.splitlines() if source else []

    def __init__(self, message: str, line: int = 0, column: int = 0, source_line: str = ''):
        self.message = message
        self.line = line
        self.column = column
        if not source_line and self.SOURCE_LINES and 1 <= line <= len(self.SOURCE_LINES):
            source_line = self.SOURCE_LINES[line - 1]
        msg = f"Parser Error [Line {line}, Col {column}]: {message}"
        if source_line:
            pointer = ' ' * max(0, column - 1) + '^'
            msg = chr(10).join([msg, '    ' + source_line.strip(), '    ' + pointer])
        super().__init__(msg)


class Parser:
    def __init__(self, tokens: List[Token], filename: str = "main.fox", source: str = ""):
        if source:
            ParserError.set_source(source)
        self.tokens = tokens
        self.pos = 0
        self.filename = filename

    def _peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def _match(self, *types: TokenType) -> bool:
        if self._peek().type in types:
            self.pos += 1
            return True
        return False

    def _consume(self, type_: TokenType, message: str) -> Token:
        tok = self._peek()
        if tok.type == type_:
            self.pos += 1
            return tok
        raise ParserError(message, tok.line, tok.column)

    def _skip_newlines(self):
        while self._peek().type == TokenType.NEWLINE:
            self.pos += 1

    def _skip_layout(self):
        while self._peek().type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
            self.pos += 1

    def parse(self) -> Program:
        statements = []
        self._skip_newlines()
        while self._peek().type != TokenType.EOF:
            stmt = self._parse_statement()
            if stmt:
                statements.append(stmt)
            self._skip_newlines()
        return Program(statements, self.filename)

    def _parse_statement(self) -> Optional[ASTNode]:
        self._skip_newlines()
        tok = self._peek()

        if tok.type == TokenType.ACT:
            return self._parse_act()
        if tok.type == TokenType.MOLD:
            return self._parse_mold()
        if tok.type == TokenType.PICK:
            return self._parse_pick()
        if tok.type == TokenType.PULSE:
            return self._parse_pulse()
        if tok.type == TokenType.SPIN:
            return self._parse_spin()
        if tok.type == TokenType.CYCLE:
            return self._parse_cycle()
        if tok.type == TokenType.GUARD:
            return self._parse_guard()
        if tok.type == TokenType.TRAP:
            return self._parse_trap()
        if tok.type == TokenType.FUSE:
            return self._parse_fuse()
        if tok.type == TokenType.LOCK:
            return self._parse_lock()
        if tok.type == TokenType.SHIFT:
            return self._parse_shift()
        if tok.type == TokenType.EMIT:
            return self._parse_emit()
        if tok.type == TokenType.HALT:
            self.pos += 1
            return HaltStmt(tok.line, tok.column)
        if tok.type == TokenType.SKIP:
            self.pos += 1
            return SkipStmt(tok.line, tok.column)
        if tok.type == TokenType.SAY:
            return self._parse_say()

        expr = self._parse_expression()
        
        # Check if this expression is the left-hand target of an assignment (=, +=, -=, *=, /=)
        next_tok = self._peek()
        if next_tok.type in (TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN, TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN):
            op_type = next_tok.type
            self.pos += 1
            rhs = self._parse_expression()
            if op_type == TokenType.ASSIGN:
                return AssignmentStatement(expr, rhs, tok.line, tok.column)
            
            op_map = {
                TokenType.PLUS_ASSIGN: "+", TokenType.MINUS_ASSIGN: "-",
                TokenType.STAR_ASSIGN: "*", TokenType.SLASH_ASSIGN: "/"
            }
            expanded = BinaryOp(expr, op_map[op_type], rhs, tok.line, tok.column)
            return AssignmentStatement(expr, expanded, tok.line, tok.column)

        return expr

    def _parse_block(self) -> List[ASTNode]:
        self._consume(TokenType.INDENT, "Expected indented block")
        body = []
        while self._peek().type not in (TokenType.DEDENT, TokenType.EOF):
            self._skip_newlines()
            if self._peek().type in (TokenType.DEDENT, TokenType.EOF):
                break
            body.append(self._parse_statement())
            self._skip_newlines()
        self._consume(TokenType.DEDENT, "Expected dedent after block")
        return body

    def _parse_act(self) -> ActDef:
        tok = self._consume(TokenType.ACT, "Expected 'act'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected act name")
        self._consume(TokenType.LPAREN, "Expected '(' after act name")
        params = []
        if self._peek().type != TokenType.RPAREN:
            params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name").value)
            while self._match(TokenType.COMMA):
                params.append(self._consume(TokenType.IDENTIFIER, "Expected parameter name").value)
        self._consume(TokenType.RPAREN, "Expected ')'")
        self._skip_newlines()
        body = self._parse_block()
        return ActDef(name_tok.value, params, body, tok.line, tok.column)

    def _parse_mold(self) -> MoldDef:
        tok = self._consume(TokenType.MOLD, "Expected 'mold'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected blueprint name")
        self._consume(TokenType.LBRACE, "Expected '{'")
        fields = {}
        self._skip_layout()
        while self._peek().type != TokenType.RBRACE and self._peek().type != TokenType.EOF:
            k_tok = self._consume(TokenType.IDENTIFIER, "Expected field name")
            self._consume(TokenType.COLON, "Expected ':'")
            v_expr = self._parse_expression()
            fields[k_tok.value] = v_expr
            self._match(TokenType.COMMA)
            self._skip_layout()
        self._consume(TokenType.RBRACE, "Expected '}'")
        return MoldDef(name_tok.value, fields, tok.line, tok.column)

    def _parse_pick(self) -> PickStatement:
        tok = self._consume(TokenType.PICK, "Expected 'pick'")
        cond = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()
        
        alts = []
        self._skip_newlines()
        while self._peek().type == TokenType.ALT:
            self._consume(TokenType.ALT, "Expected 'alt'")
            alt_cond = self._parse_expression()
            self._skip_newlines()
            alt_body = self._parse_block()
            alts.append((alt_cond, alt_body))
            self._skip_newlines()

        otherwise_body = None
        if self._peek().type == TokenType.OTHERWISE:
            self._consume(TokenType.OTHERWISE, "Expected 'otherwise'")
            self._skip_newlines()
            otherwise_body = self._parse_block()

        return PickStatement(cond, body, alts, otherwise_body, tok.line, tok.column)

    def _parse_pulse(self) -> PulseStatement:
        tok = self._consume(TokenType.PULSE, "Expected 'pulse'")
        var_tok = self._consume(TokenType.IDENTIFIER, "Expected delta variable")
        self._skip_newlines()
        body = self._parse_block()
        return PulseStatement(var_tok.value, body, tok.line, tok.column)

    def _parse_spin(self) -> SpinStatement:
        tok = self._consume(TokenType.SPIN, "Expected 'spin'")
        cond = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()
        return SpinStatement(cond, body, tok.line, tok.column)

    def _parse_cycle(self) -> CycleStatement:
        tok = self._consume(TokenType.CYCLE, "Expected 'cycle'")
        var_tok = self._consume(TokenType.IDENTIFIER, "Expected loop variable")
        if self._peek().type == TokenType.IDENTIFIER and self._peek().value == "in":
            self.pos += 1
        count_expr = self._parse_expression()
        self._skip_newlines()
        body = self._parse_block()
        return CycleStatement(var_tok.value, count_expr, body, tok.line, tok.column)

    def _parse_guard(self) -> GuardStatement:
        tok = self._consume(TokenType.GUARD, "Expected 'guard'")
        cond = self._parse_expression()
        return GuardStatement(cond, tok.line, tok.column)

    def _parse_trap(self) -> TrapStatement:
        tok = self._consume(TokenType.TRAP, "Expected 'trap'")
        self._skip_newlines()
        try_body = self._parse_block()
        catch_body = None
        self._skip_newlines()
        if self._peek().type == TokenType.OTHERWISE:
            self._consume(TokenType.OTHERWISE, "Expected 'otherwise'")
            self._skip_newlines()
            catch_body = self._parse_block()
        return TrapStatement(try_body, catch_body, tok.line, tok.column)

    def _parse_fuse(self) -> FuseStatement:
        tok = self._consume(TokenType.FUSE, "Expected 'fuse'")
        mod_tok = self._consume(TokenType.IDENTIFIER, "Expected module name")
        return FuseStatement(mod_tok.value, tok.line, tok.column)

    def _parse_lock(self) -> LockStatement:
        tok = self._consume(TokenType.LOCK, "Expected 'lock'")
        name_tok = self._consume(TokenType.IDENTIFIER, "Expected identifier")
        self._consume(TokenType.ASSIGN, "Expected '='")
        expr = self._parse_expression()
        return LockStatement(name_tok.value, expr, tok.line, tok.column)

    def _parse_shift(self) -> ShiftStatement:
        tok = self._consume(TokenType.SHIFT, "Expected 'shift'")
        target = self._parse_statement()
        return ShiftStatement(target, tok.line, tok.column)

    def _parse_emit(self) -> EmitStmt:
        tok = self._consume(TokenType.EMIT, "Expected 'emit'")
        val = None
        if self._peek().type not in (TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            val = self._parse_expression()
        return EmitStmt(val, tok.line, tok.column)

    def _parse_say(self) -> SayStatement:
        tok = self._consume(TokenType.SAY, "Expected 'say'")
        expr = self._parse_expression()
        return SayStatement(expr, tok.line, tok.column)

    def _parse_expression(self) -> ASTNode:
        return self._parse_logical_either()

    def _parse_logical_either(self) -> ASTNode:
        node = self._parse_logical_also()
        while self._match(TokenType.EITHER):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_logical_also()
            node = BinaryOp(node, "either", right, op_tok.line, op_tok.column)
        return node

    def _parse_logical_also(self) -> ASTNode:
        node = self._parse_equality()
        while self._match(TokenType.ALSO):
            op_tok = self.tokens[self.pos - 1]
            right = self._parse_equality()
            node = BinaryOp(node, "also", right, op_tok.line, op_tok.column)
        return node

    def _parse_equality(self) -> ASTNode:
        node = self._parse_comparison()
        while self._peek().type in (TokenType.EQ, TokenType.NEQ):
            op_tok = self._peek()
            self.pos += 1
            right = self._parse_comparison()
            node = BinaryOp(node, op_tok.value, right, op_tok.line, op_tok.column)
        return node

    def _parse_comparison(self) -> ASTNode:
        node = self._parse_additive()
        while self._peek().type in (TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            op_tok = self._peek()
            self.pos += 1
            right = self._parse_additive()
            node = BinaryOp(node, op_tok.value, right, op_tok.line, op_tok.column)
        return node

    def _parse_additive(self) -> ASTNode:
        node = self._parse_multiplicative()
        while self._peek().type in (TokenType.PLUS, TokenType.MINUS):
            op_tok = self._peek()
            self.pos += 1
            right = self._parse_multiplicative()
            node = BinaryOp(node, op_tok.value, right, op_tok.line, op_tok.column)
        return node

    def _parse_multiplicative(self) -> ASTNode:
        node = self._parse_unary()
        while self._peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op_tok = self._peek()
            self.pos += 1
            right = self._parse_unary()
            node = BinaryOp(node, op_tok.value, right, op_tok.line, op_tok.column)
        return node

    def _parse_unary(self) -> ASTNode:
        if self._peek().type in (TokenType.DENY, TokenType.MINUS):
            op_tok = self._peek()
            self.pos += 1
            operand = self._parse_unary()
            return UnaryOp(op_tok.value if op_tok.type == TokenType.MINUS else "deny", operand, op_tok.line, op_tok.column)
        return self._parse_postfix()

    def _parse_postfix(self) -> ASTNode:
        node = self._parse_primary()
        while True:
            if self._match(TokenType.DOT):
                member_tok = self._consume(TokenType.IDENTIFIER, "Expected member name")
                node = MemberAccess(node, member_tok.value, member_tok.line, member_tok.column)
            elif self._match(TokenType.LBRACKET):
                self._skip_layout()
                idx_expr = self._parse_expression()
                self._skip_layout()
                self._consume(TokenType.RBRACKET, "Expected ']' after index")
                node = IndexAccess(node, idx_expr, self._peek().line, self._peek().column)
            else:
                break
        return node

    def _parse_primary(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.ASK:
            self.pos += 1
            prompt = None
            if self._peek().type in (TokenType.STRING, TokenType.IDENTIFIER):
                prompt = self._parse_expression()
            return AskExpression(prompt, tok.line, tok.column)

        if tok.type == TokenType.NUMBER:
            self.pos += 1
            return NumberLiteral(tok.value, tok.line, tok.column)

        if tok.type == TokenType.STRING:
            self.pos += 1
            return StringLiteral(tok.value, tok.line, tok.column)

        if tok.type == TokenType.AYE:
            self.pos += 1
            return BooleanLiteral(True, tok.line, tok.column)

        if tok.type == TokenType.NAY:
            self.pos += 1
            return BooleanLiteral(False, tok.line, tok.column)

        if tok.type == TokenType.BLANK:
            self.pos += 1
            return BlankLiteral(tok.line, tok.column)

        # Multi-line lists: [a, b, c]
        if tok.type == TokenType.LBRACKET:
            self.pos += 1
            elements = []
            self._skip_layout()
            if self._peek().type != TokenType.RBRACKET:
                elements.append(self._parse_expression())
                self._skip_layout()
                while self._match(TokenType.COMMA):
                    self._skip_layout()
                    if self._peek().type == TokenType.RBRACKET:
                        break
                    elements.append(self._parse_expression())
                    self._skip_layout()
            self._consume(TokenType.RBRACKET, "Expected ']'")
            return ListLiteral(elements, tok.line, tok.column)

        # Multi-line packs: { key: val }
        if tok.type in (TokenType.PACK, TokenType.LBRACE):
            self.pos += 1
            if tok.type == TokenType.PACK:
                self._consume(TokenType.LBRACE, "Expected '{'")
            entries = {}
            self._skip_layout()
            while self._peek().type != TokenType.RBRACE and self._peek().type != TokenType.EOF:
                k_tok = self._consume(TokenType.IDENTIFIER, "Expected key")
                self._consume(TokenType.COLON, "Expected ':'")
                v_expr = self._parse_expression()
                entries[k_tok.value] = v_expr
                self._match(TokenType.COMMA)
                self._skip_layout()
            self._consume(TokenType.RBRACE, "Expected '}'")
            return PackLiteral(entries, tok.line, tok.column)

        if tok.type == TokenType.IDENTIFIER:
            self.pos += 1
            if self._match(TokenType.LPAREN):
                args = []
                self._skip_layout()
                if self._peek().type != TokenType.RPAREN:
                    args.append(self._parse_expression())
                    self._skip_layout()
                    while self._match(TokenType.COMMA):
                        self._skip_layout()
                        if self._peek().type == TokenType.RPAREN:
                            break
                        args.append(self._parse_expression())
                        self._skip_layout()
                self._consume(TokenType.RPAREN, "Expected ')'")
                return CallExpression(tok.value, args, tok.line, tok.column)
            return Identifier(tok.value, tok.line, tok.column)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')'")
            return expr

        raise ParserError(f"Unexpected token '{tok.value}' ({tok.type.name})", tok.line, tok.column)

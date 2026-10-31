import unittest
from engine.lexer import Lexer
from engine.parser import (
    Parser, ParserError, SayStatement, AssignmentStatement,
    BinaryOp, CallExpression, LoadStatement, SpaceStatement,
    EntityStatement, ReplicateStatement, ConnectStatement
)

class TestFoxVCParser(unittest.TestCase):
    def test_parse_say_string(self):
        tokens = Lexer('say "hello"').tokenize()
        prog = Parser(tokens).parse()
        self.assertEqual(len(prog.statements), 1)
        self.assertIsInstance(prog.statements[0], SayStatement)

    def test_parse_say_rejects_comma(self):
        tokens = Lexer('say "a", "b"').tokenize()
        with self.assertRaises(ParserError) as ctx:
            Parser(tokens).parse()
        self.assertIn("Commas are not used", str(ctx.exception))

    def test_parse_assignment(self):
        tokens = Lexer('x = 42 + 8').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, AssignmentStatement)
        self.assertEqual(stmt.name, "x")
        self.assertIsInstance(stmt.expression, BinaryOp)

    def test_parse_operator_precedence(self):
        tokens = Lexer('x = 2 + 3 * 4').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt.expression, BinaryOp)
        self.assertEqual(stmt.expression.op, "+")
        self.assertEqual(stmt.expression.right.op, "*")

    def test_parse_boolean_logic(self):
        tokens = Lexer('res = true and false or not true').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt.expression, BinaryOp)

    def test_parse_function_call(self):
        tokens = Lexer('f = force(50, 2)').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt.expression, CallExpression)
        self.assertEqual(stmt.expression.callee, "force")
        self.assertEqual(len(stmt.expression.args), 2)

    def test_parse_load_statement_simple(self):
        tokens = Lexer('load "mathx"').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, LoadStatement)
        self.assertEqual(stmt.module_name, "mathx")

    def test_parse_load_version_and_alias(self):
        tokens = Lexer('load "spatial.expansion" version "^1.0.0" as spat').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertEqual(stmt.module_name, "spatial.expansion")
        self.assertEqual(stmt.version_constraint, "^1.0.0")
        self.assertEqual(stmt.alias, "spat")

    def test_parse_shelf_statement(self):
        tokens = Lexer('shelf "physics"').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, LoadStatement)
        self.assertEqual(stmt.module_name, "physics")

    def test_parse_call_shelf_statement(self):
        tokens = Lexer('call shelf "mathx"').tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, LoadStatement)
        self.assertEqual(stmt.module_name, "mathx")

    def test_parse_space_and_entity(self):
        src = "space World\n    entity Core form circle diameter 30"
        tokens = Lexer(src).tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, SpaceStatement)
        self.assertEqual(stmt.name, "World")
        self.assertIsInstance(stmt.body[0], EntityStatement)

    def test_parse_replicate_statement(self):
        src = "replicate 4 of entity Particle\n    form circle diameter 5"
        tokens = Lexer(src).tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, ReplicateStatement)
        self.assertEqual(stmt.count, 4)
        self.assertEqual(stmt.entity_name, "Particle")

    def test_parse_connect_statement(self):
        src = "connect Axle from Wheel1 to Wheel2\n    thickness 3.0"
        tokens = Lexer(src).tokenize()
        prog = Parser(tokens).parse()
        stmt = prog.statements[0]
        self.assertIsInstance(stmt, ConnectStatement)
        self.assertEqual(stmt.name, "Axle")
        self.assertEqual(stmt.from_spec, "Wheel1")
        self.assertEqual(stmt.to_spec, "Wheel2")

    def test_parse_ask_expression(self):
        tokens = Lexer('name = ask "Enter name"').tokenize()
        prog = Parser(tokens).parse()
        self.assertEqual(prog.statements[0].name, "name")

    def test_parse_unexpected_token_error(self):
        tokens = Lexer('unknowninstruction foo').tokenize()
        with self.assertRaises(ParserError):
            Parser(tokens).parse()

if __name__ == '__main__':
    unittest.main()

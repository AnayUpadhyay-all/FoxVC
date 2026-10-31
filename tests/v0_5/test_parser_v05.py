import unittest
from engine.lexer import Lexer
from engine.parser import Parser
from engine.interpreter import Interpreter

class TestFoxVCBehaviorV05(unittest.TestCase):
    def setUp(self):
        self.interp = Interpreter()

    def test_trap_block_execution(self):
        src = """
status = "initial"
trap
    status = "inside_trap"
otherwise
    status = "recovered"
"""
        ast = Parser(Lexer(src).tokenize()).parse()
        self.interp.reset()
        self.interp.execute(ast)
        self.assertEqual(self.interp.variables.get('status'), 'inside_trap')

    def test_act_definition_and_call(self):
        src = """
act add_nums(a, b)
    emit a + b

total = add_nums(25, 17)
"""
        ast = Parser(Lexer(src).tokenize()).parse()
        self.interp.reset()
        self.interp.execute(ast)
        self.assertEqual(self.interp.variables.get('total'), 42)

if __name__ == '__main__':
    unittest.main()

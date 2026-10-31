import unittest
from engine.lexer import Lexer, TokenType

class TestFoxVCLexerV05(unittest.TestCase):
    def test_numbers_and_arithmetic(self):
        src = "10 + 20.5 * 3 - 4 / 2"
        tokens = Lexer(src).tokenize()
        types = [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertIn(TokenType.NUMBER, types)
        self.assertIn(TokenType.PLUS, types)
        self.assertIn(TokenType.STAR, types)

    def test_keywords_v05(self):
        src = "pick otherwise pulse dt trap emit halt skip also either say act"
        tokens = Lexer(src).tokenize()
        types = [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
        self.assertIn(TokenType.PICK, types)
        self.assertIn(TokenType.OTHERWISE, types)
        self.assertIn(TokenType.TRAP, types)
        self.assertIn(TokenType.EMIT, types)
        self.assertIn(TokenType.HALT, types)
        self.assertIn(TokenType.SKIP, types)

    def test_string_tokenization(self):
        src = 'say "Hello FoxVC v0.5.4"'
        tokens = Lexer(src).tokenize()
        str_tokens = [t for t in tokens if t.type == TokenType.STRING]
        self.assertEqual(len(str_tokens), 1)
        self.assertEqual(str_tokens[0].value, "Hello FoxVC v0.5.4")

if __name__ == '__main__':
    unittest.main()

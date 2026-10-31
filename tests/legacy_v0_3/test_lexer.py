import unittest
from engine.lexer import Lexer, LexerError, TokenType

class TestFoxVCLexer(unittest.TestCase):
    def test_tokenize_integers(self):
        tokens = Lexer("42 100 0").tokenize()
        nums = [t.value for t in tokens if t.type == TokenType.NUMBER]
        self.assertEqual(nums, [42, 100, 0])

    def test_tokenize_floats(self):
        tokens = Lexer("3.14 0.5 120.0").tokenize()
        nums = [t.value for t in tokens if t.type == TokenType.NUMBER]
        self.assertEqual(nums, [3.14, 0.5, 120.0])

    def test_tokenize_strings_double_quoted(self):
        tokens = Lexer('"hello world" "foxvc"').tokenize()
        strs = [t.value for t in tokens if t.type == TokenType.STRING]
        self.assertEqual(strs, ["hello world", "foxvc"])

    def test_tokenize_escape_sequences(self):
        tokens = Lexer(r'"line1\nline2\t\"quoted\""').tokenize()
        strs = [t.value for t in tokens if t.type == TokenType.STRING]
        self.assertEqual(strs[0], 'line1\nline2\t"quoted"')

    def test_reject_apostrophe(self):
        with self.assertRaises(LexerError) as ctx:
            Lexer("'single quoted'").tokenize()
        self.assertIn("Apostrophes are not used", str(ctx.exception))

    def test_reject_semicolon(self):
        with self.assertRaises(LexerError) as ctx:
            Lexer("x = 10;").tokenize()
        self.assertIn("Semicolons are not used", str(ctx.exception))

    def test_unterminated_string_error(self):
        with self.assertRaises(LexerError) as ctx:
            Lexer('"unterminated string').tokenize()
        self.assertIn("Unterminated string", str(ctx.exception))

    def test_tokenize_booleans(self):
        tokens = Lexer("true false TRUE FALSE").tokenize()
        bools = [t.value for t in tokens if t.type == TokenType.BOOLEAN]
        self.assertEqual(bools, [True, False, True, False])

    def test_tokenize_arithmetic_operators(self):
        tokens = Lexer("+ - * / =").tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(types, [TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.ASSIGN])

    def test_tokenize_comparisons(self):
        tokens = Lexer("== != <= >= < >").tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(types, [TokenType.EQ, TokenType.NEQ, TokenType.LTE, TokenType.GTE, TokenType.LT, TokenType.GT])

    def test_tokenize_comments_ignored(self):
        tokens = Lexer("x = 10 # This is a comment\ny = 20").tokenize()
        idents = [t.value for t in tokens if t.type == TokenType.IDENTIFIER]
        self.assertEqual(idents, ["x", "y"])

    def test_tokenize_indent_dedent(self):
        src = "space S\n    entity E\n        form circle"
        tokens = Lexer(src).tokenize()
        types = [t.type for t in tokens]
        self.assertIn(TokenType.INDENT, types)
        self.assertIn(TokenType.DEDENT, types)

    def test_tokenize_parentheses_and_brackets(self):
        tokens = Lexer("(1, 2) [3, 4]").tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(types, [
            TokenType.LPAREN, TokenType.NUMBER, TokenType.COMMA, TokenType.NUMBER, TokenType.RPAREN,
            TokenType.LBRACKET, TokenType.NUMBER, TokenType.COMMA, TokenType.NUMBER, TokenType.RBRACKET
        ])

    def test_tokenize_keywords(self):
        tokens = Lexer("say ask set add render bind mount load call shelf").tokenize()
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        self.assertEqual(types, [
            TokenType.SAY, TokenType.ASK, TokenType.SET, TokenType.ADD, TokenType.RENDER,
            TokenType.BIND, TokenType.MOUNT, TokenType.LOAD, TokenType.CALL, TokenType.SHELF
        ])

    def test_unexpected_character(self):
        with self.assertRaises(LexerError):
            Lexer("x = 10 @ 20").tokenize()

if __name__ == '__main__':
    unittest.main()

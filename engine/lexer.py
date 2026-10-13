"""
FoxVC Lexer Engine (v0.5.2x)
Zero-Overlap 25 Keywords + strict string validation.
"""

from enum import Enum, auto
from typing import List, Optional, Any


class TokenType(Enum):
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()
    
    # Operators & Compounds
    ASSIGN = auto()         # =
    PLUS_ASSIGN = auto()    # +=
    MINUS_ASSIGN = auto()   # -=
    STAR_ASSIGN = auto()    # *=
    SLASH_ASSIGN = auto()   # /=
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    PERCENT = auto()        # %
    
    # Comparisons
    EQ = auto()             # ==
    NEQ = auto()            # !=
    LT = auto()             # <
    LTE = auto()            # <=
    GT = auto()             # >
    GTE = auto()            # >=
    
    # Delimiters
    LPAREN = auto()         # (
    RPAREN = auto()         # )
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    COMMA = auto()          # ,
    COLON = auto()          # :
    DOT = auto()            # .
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    EOF = auto()
    
    # 25 Zero-Overlap Core Keywords
    ACT = auto()
    EMIT = auto()
    PACK = auto()
    MOLD = auto()
    PICK = auto()
    ALT = auto()
    OTHERWISE = auto()
    PULSE = auto()
    CYCLE = auto()
    SPIN = auto()
    HALT = auto()
    SKIP = auto()
    SAY = auto()
    ASK = auto()
    GUARD = auto()
    TRAP = auto()
    RECOVER = auto()
    FUSE = auto()
    LOCK = auto()
    SHIFT = auto()
    BLANK = auto()
    AYE = auto()
    NAY = auto()
    ALSO = auto()
    EITHER = auto()
    DENY = auto()


class LexerError(Exception):
    def __init__(self, message: str, line: int = 0, column: int = 0):
        super().__init__(f"Lexer Error [Line {line}, Col {column}]: {message}")
        self.message = message
        self.line = line
        self.column = column


class Token:
    def __init__(self, type_: TokenType, value: Any, line: int, column: int):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"


KEYWORDS = {
    "act": TokenType.ACT,
    "emit": TokenType.EMIT,
    "pack": TokenType.PACK,
    "mold": TokenType.MOLD,
    "pick": TokenType.PICK,
    "alt": TokenType.ALT,
    "otherwise": TokenType.OTHERWISE,
    "pulse": TokenType.PULSE,
    "cycle": TokenType.CYCLE,
    "spin": TokenType.SPIN,
    "halt": TokenType.HALT,
    "skip": TokenType.SKIP,
    "say": TokenType.SAY,
    "ask": TokenType.ASK,
    "guard": TokenType.GUARD,
    "trap": TokenType.TRAP,
    "recover": TokenType.RECOVER,
    "fuse": TokenType.FUSE,
    "lock": TokenType.LOCK,
    "shift": TokenType.SHIFT,
    "blank": TokenType.BLANK,
    "aye": TokenType.AYE,
    "nay": TokenType.NAY,
    "also": TokenType.ALSO,
    "either": TokenType.EITHER,
    "deny": TokenType.DENY,
}


class Lexer:
    def __init__(self, source_code: str, filename: str = "main.fox"):
        self.source = source_code
        self.filename = filename
        self.tokens: List[Token] = []
        self.indent_stack = [0]

    def tokenize(self) -> List[Token]:
        lines = self.source.splitlines(keepends=True)
        self.tokens = []
        self.indent_stack = [0]

        for line_num, line_text in enumerate(lines, start=1):
            stripped = line_text.strip()
            if not stripped or stripped.startswith("#"):
                continue

            leading_spaces = len(line_text) - len(line_text.lstrip(' '))
            current_indent = self.indent_stack[-1]

            if leading_spaces > current_indent:
                self.indent_stack.append(leading_spaces)
                self.tokens.append(Token(TokenType.INDENT, leading_spaces, line_num, 1))
            else:
                while leading_spaces < self.indent_stack[-1]:
                    self.indent_stack.pop()
                    self.tokens.append(Token(TokenType.DEDENT, leading_spaces, line_num, 1))

            idx = leading_spaces
            line_len = len(line_text)
            while idx < line_len:
                ch = line_text[idx]

                if ch in (' ', '\t', '\r'):
                    idx += 1
                    continue
                if ch == '\n' or ch == '#':
                    break

                col = idx + 1
                pair = line_text[idx:idx+2]

                if pair == "+=":
                    self.tokens.append(Token(TokenType.PLUS_ASSIGN, "+=", line_num, col))
                    idx += 2; continue
                if pair == "-=":
                    self.tokens.append(Token(TokenType.MINUS_ASSIGN, "-=", line_num, col))
                    idx += 2; continue
                if pair == "*=":
                    self.tokens.append(Token(TokenType.STAR_ASSIGN, "*=", line_num, col))
                    idx += 2; continue
                if pair == "/=":
                    self.tokens.append(Token(TokenType.SLASH_ASSIGN, "/=", line_num, col))
                    idx += 2; continue
                if pair == "==":
                    self.tokens.append(Token(TokenType.EQ, "==", line_num, col))
                    idx += 2; continue
                if pair == "!=":
                    self.tokens.append(Token(TokenType.NEQ, "!=", line_num, col))
                    idx += 2; continue
                if pair == "<=":
                    self.tokens.append(Token(TokenType.LTE, "<=", line_num, col))
                    idx += 2; continue
                if pair == ">=":
                    self.tokens.append(Token(TokenType.GTE, ">=", line_num, col))
                    idx += 2; continue

                single_map = {
                    '=': TokenType.ASSIGN, '+': TokenType.PLUS, '-': TokenType.MINUS,
                    '*': TokenType.STAR, '/': TokenType.SLASH, '%': TokenType.PERCENT,
                    '<': TokenType.LT, '>': TokenType.GT, '(': TokenType.LPAREN,
                    ')': TokenType.RPAREN, '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                    '[': TokenType.LBRACKET, ']': TokenType.RBRACKET, ',': TokenType.COMMA,
                    ':': TokenType.COLON, '.': TokenType.DOT
                }
                if ch in single_map:
                    self.tokens.append(Token(single_map[ch], ch, line_num, col))
                    idx += 1
                    continue

                if ch in ('"', "'"):
                    quote = ch
                    idx += 1
                    start_col = col
                    str_chars = []
                    found_end = False
                    while idx < line_len:
                        if line_text[idx] == quote:
                            found_end = True
                            idx += 1
                            break
                        if line_text[idx] == '\\' and idx + 1 < line_len:
                            idx += 1
                            str_chars.append(line_text[idx])
                        else:
                            str_chars.append(line_text[idx])
                        idx += 1

                    if not found_end:
                        raise LexerError(f"Unclosed string literal starting with {quote}", line_num, start_col)

                    self.tokens.append(Token(TokenType.STRING, "".join(str_chars), line_num, start_col))
                    continue

                if ch.isdigit():
                    num_chars = []
                    start_col = col
                    has_dot = False
                    while idx < line_len and (line_text[idx].isdigit() or (line_text[idx] == '.' and not has_dot)):
                        if line_text[idx] == '.':
                            if idx + 1 < line_len and not line_text[idx + 1].isdigit():
                                break
                            has_dot = True
                        num_chars.append(line_text[idx])
                        idx += 1
                    val = float("".join(num_chars)) if has_dot else int("".join(num_chars))
                    self.tokens.append(Token(TokenType.NUMBER, val, line_num, start_col))
                    continue

                if ch.isalpha() or ch == '_':
                    id_chars = []
                    start_col = col
                    while idx < line_len and (line_text[idx].isalnum() or line_text[idx] == '_'):
                        id_chars.append(line_text[idx])
                        idx += 1
                    ident = "".join(id_chars)
                    tok_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
                    self.tokens.append(Token(tok_type, ident, line_num, start_col))
                    continue

                idx += 1

            self.tokens.append(Token(TokenType.NEWLINE, "\n", line_num, len(line_text)))

        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 0, len(lines), 1))

        self.tokens.append(Token(TokenType.EOF, "", len(lines) + 1, 1))
        return self.tokens

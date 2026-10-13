"""
FoxVC Core Engine (v0.5.4)
"""

from .lexer import Lexer, LexerError, Token, TokenType
from .parser import Parser, ParserError
from .interpreter import Interpreter, FoxPack, RuntimeError
from .runner import run_foxvc_code, run_foxvc_project, run_foxvc_diagnostic

__all__ = [
    "Lexer",
    "LexerError",
    "Token",
    "TokenType",
    "Parser",
    "ParserError",
    "Interpreter",
    "FoxPack",
    "RuntimeError",
    "run_foxvc_code",
    "run_foxvc_project",
    "run_foxvc_diagnostic",
]

__version__ = '0.5.4'

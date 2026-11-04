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

from .version import FOXVC_LANGUAGE_VERSION, FOXVC_ENGINE_VERSION, FOXVC_RUNTIME_VERSION

__version__ = FOXVC_ENGINE_VERSION

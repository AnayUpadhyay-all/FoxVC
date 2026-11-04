"""
Fox Den Studio Services (Headless).
Decouples execution, evaluation, and diagnostics from GUI frameworks.
"""

from typing import Dict, Any, Optional
from engine.runner import run_foxvc, format_fox_diagnostic
from engine.lexer import Lexer, LexerError
from engine.parser import Parser, ParserError


class StudioExecutionService:
    """Headless execution service for Studio desktop, CLI, and Web engines."""
    @staticmethod
    def execute(
        source: str,
        engine_mode: str = "interp",
        sandboxed: bool = False,
        allowed_dir: Optional[str] = None,
        timeout: Optional[float] = None,
        file_path: Optional[str] = None
    ) -> Any:
        return run_foxvc(
            source=source,
            engine_mode=engine_mode,
            sandboxed=sandboxed,
            allowed_dir=allowed_dir,
            timeout=timeout,
            file_path=file_path,
            as_result=True
        )


class StudioDiagnosticsService:
    """Headless diagnostics inspection service."""
    @staticmethod
    def validate_syntax(source: str, filename: str = "main.fox") -> Dict[str, Any]:
        try:
            tokens = Lexer(source, filename=filename).tokenize()
            Parser(tokens, filename=filename, source=source).parse()
            return {"valid": True, "error": None, "diagnostics": []}
        except (LexerError, ParserError) as err:
            return {
                "valid": False,
                "error": str(err),
                "line": getattr(err, "line", 1),
                "column": getattr(err, "column", 1),
                "filename": filename
            }

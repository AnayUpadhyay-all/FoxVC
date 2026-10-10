"""
FoxVC Runtime Definitions and Execution Context (v0.5.0)
Defines metadata, diagnostics, reporting structures, and execution results.
"""

from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field

FOXVC_LANGUAGE_VERSION = "0.5.1"
FOXVC_RUNTIME_VERSION = "0.5.0"

class SourceFormat:
    STANDARD = "fox"
    STRUCTURE = "fweb"
    SKIN = "fskin"
    LOGIC = "flogic"

class DiagnosticCategory:
    SYNTAX = "SYNTAX"
    TYPE = "TYPE"
    NAME = "NAME"
    MATH = "MATH"
    SECURITY = "SECURITY"
    PROJECT = "PROJECT"
    RUNTIME = "RUNTIME"
    INTERNAL = "INTERNAL"

class DiagnosticSeverity:
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class Diagnostic:
    message: str
    line: int
    column: int
    category: str = DiagnosticCategory.RUNTIME
    severity: str = DiagnosticSeverity.ERROR
    file: Optional[str] = None

class StatementStatus:
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"

@dataclass
class StatementReport:
    line: int
    source: str
    status: str
    variable: Optional[str] = None
    value: Optional[str] = None
    output: Optional[str] = None
    diagnostic: Optional[Diagnostic] = None
    blocked_reason: Optional[str] = None
    file: Optional[str] = None

@dataclass
class DiagnosticSummary:
    passed: int = 0
    failed: int = 0
    blocked: int = 0

@dataclass
class ExecutionResult:
    success: bool
    output: str = ""
    diagnostics: List[Diagnostic] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    statement_reports: List[StatementReport] = field(default_factory=list)
    summary: Optional[DiagnosticSummary] = None

    @property
    def error(self) -> Optional[str]:
        if not self.success and self.diagnostics:
            d = self.diagnostics[0]
            loc = f" [{d.file}]" if d.file else ""
            return f"Runtime Error{loc} [Line {d.line}, Col {d.column}]: {d.message}"
        return None

    @property
    def is_web_app(self) -> bool:
        return "web_app" in self.metadata

    @property
    def web_app(self) -> Any:
        return self.metadata.get("web_app")

    @property
    def web_output(self) -> str:
        return self.metadata.get("web_output", "")

    @property
    def spatial_space(self) -> Any:
        return self.metadata.get("spatial_space")

    @property
    def svg_output(self) -> str:
        return self.metadata.get("svg_output", "")

InputSink = Callable[[str], str]
OutputSink = Callable[[str], None]

class FallbackSpatialObject:
    """Compatibility shim for legacy spatial references."""
    def __init__(self, name="Fallback"):
        self.name = name

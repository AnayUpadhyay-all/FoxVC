"""
Fox Den Studio Package (v0.6.0-alpha).
Provides decoupled headless services, desktop GUI, and Web Studio.
"""

from .services import StudioExecutionService, StudioDiagnosticsService
from .web_engine import execute_foxvc_source

try:
    from .app import FoxVCStudio, main
    FoxVCStudioApp = FoxVCStudio
    __all__ = [
        "FoxVCStudio",
        "FoxVCStudioApp",
        "main",
        "StudioExecutionService",
        "StudioDiagnosticsService",
        "execute_foxvc_source",
    ]
except Exception:
    __all__ = [
        "StudioExecutionService",
        "StudioDiagnosticsService",
        "execute_foxvc_source",
    ]

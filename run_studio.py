#!/usr/bin/env python3
"""
FoxVC Studio Entry Launcher
Supports direct execution and file argument passing from any working directory.
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from studio.app import main

if __name__ == "__main__":
    sys.exit(main() or 0)

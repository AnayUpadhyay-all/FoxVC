#!/usr/bin/env python3
import os
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from studio.app import FoxVCStudioApp, main

if __name__ == "__main__":
    sys.exit(main() or 0)

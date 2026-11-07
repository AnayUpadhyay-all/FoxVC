#!/usr/bin/env python3
"""
FoxCloud Gaming Entry Launcher
Run this on your Samsung Galaxy F34 5G (or PC) to start hosting cloud games.
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cloud_gaming.server import start_server, PORT

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else PORT
    start_server(port)

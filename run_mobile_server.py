"""
FoxVC Mobile Studio Host Server
Serves the mobile coding environment and executes sandboxed FoxVC code over local Wi-Fi.
"""
import os
import sys

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from studio.web_studio import run_server, PORT

def start_server():
    os.chdir(REPO_ROOT)
    run_server(network=True, port=PORT)

if __name__ == "__main__":
    start_server()

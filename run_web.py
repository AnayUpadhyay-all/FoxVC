import os
import sys
import subprocess
import time
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    use_tunnel = "--public" in sys.argv or "--tunnel" in sys.argv

    print("=" * 60)
    print("  LAUNCHING FOXVC WEB STUDIO (LOCAL & SECURE)")
    print("=" * 60)
    print("\n  Local URL: http://127.0.0.1:8080\n")

    server_cmd = [sys.executable, os.path.join(ROOT_DIR, "studio", "web_studio.py")]
    server_proc = subprocess.Popen(server_cmd)
    time.sleep(1)

    if not use_tunnel:
        print("  Running locally on 127.0.0.1:8080 (Loopback only).")
        print("  To enable public tunnel sharing, restart with: python3 run_web.py --public")
        try:
            server_proc.wait()
        except KeyboardInterrupt:
            server_proc.terminate()
        return

    ngrok_bin = shutil.which("ngrok")
    if not ngrok_bin:
        print("  Notice: ngrok not found. Local web studio running on http://127.0.0.1:8080.")
        try:
            server_proc.wait()
        except KeyboardInterrupt:
            server_proc.terminate()
        return

    domain_file = os.path.join(ROOT_DIR, ".ngrok_domain")
    domain = ""
    if os.path.isfile(domain_file):
        with open(domain_file, "r", encoding="utf-8") as f:
            domain = f.read().strip()

    tunnel_cmd = [ngrok_bin, "http"]
    if domain:
        tunnel_cmd.append(f"--url={domain}")
    tunnel_cmd.append("127.0.0.1:8080")

    try:
        tunnel_proc = subprocess.Popen(tunnel_cmd)
        tunnel_proc.wait()
    except KeyboardInterrupt:
        print("\n  Shutting down FoxVC Studio...")
    finally:
        server_proc.terminate()

if __name__ == "__main__":
    main()

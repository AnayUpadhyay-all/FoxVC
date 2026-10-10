import os
import sys
import subprocess
import time
import shutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    domain_file = os.path.join(ROOT_DIR, ".ngrok_domain")
    domain = "barstool-storable-nanny.ngrok-free.dev"
    if os.path.isfile(domain_file):
        with open(domain_file, "r", encoding="utf-8") as f:
            d = f.read().strip()
            if d: domain = d

    print("=" * 60)
    print("  LAUNCHING FOXVC STUDIO (PERMANENT DOMAIN)")
    print("=" * 60)
    print(f"\n  Share this permanent link with your friends:\n   https://{domain}\n")

    server_cmd = [sys.executable, os.path.join(ROOT_DIR, "studio", "web_studio.py")]
    server_proc = subprocess.Popen(server_cmd)
    time.sleep(1)

    ngrok_bin = shutil.which("ngrok")
    if not ngrok_bin:
        print("  Notice: ngrok not found. Local web studio running on port 8080.")
        try:
            server_proc.wait()
        except KeyboardInterrupt:
            server_proc.terminate()
        return

    tunnel_cmd = [ngrok_bin, "http", f"--url={domain}", "8080"]
    try:
        tunnel_proc = subprocess.Popen(tunnel_cmd)
        tunnel_proc.wait()
    except KeyboardInterrupt:
        print("\n  Shutting down FoxVC Studio...")
    finally:
        server_proc.terminate()

if __name__ == "__main__":
    main()

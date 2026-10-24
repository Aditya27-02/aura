"""AURA — Single-command launcher for development.

Starts the FastAPI backend and Vite frontend dev server together.
Press Ctrl+C to stop both.

Usage:
    python start.py          # Start both servers
    python start.py --backend-only   # Backend only
    python start.py --port 8001      # Custom backend port
"""

import argparse
import os
import signal
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(description="AURA development launcher")
    parser.add_argument("--port", type=int, default=8000, help="Backend port (default: 8000)")
    parser.add_argument("--backend-only", action="store_true", help="Skip frontend dev server")
    args = parser.parse_args()

    env = os.environ.copy()
    env["PYTHONPATH"] = ROOT

    processes = []

    # Start backend
    backend_cmd = [
        sys.executable, "-m", "uvicorn",
        "server.main:app",
        "--host", "0.0.0.0",
        "--port", str(args.port),
    ]
    print(f"[AURA] Starting backend on http://localhost:{args.port}")
    backend = subprocess.Popen(backend_cmd, cwd=ROOT, env=env)
    processes.append(backend)

    # Start frontend (if not backend-only and frontend exists)
    frontend_dir = os.path.join(ROOT, "frontend")
    if not args.backend_only and os.path.isfile(os.path.join(frontend_dir, "package.json")):
        # Check if node_modules exists
        if not os.path.isdir(os.path.join(frontend_dir, "node_modules")):
            print("[AURA] Installing frontend dependencies...")
            subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True, check=True)

        print("[AURA] Starting frontend on http://localhost:5173")
        frontend = subprocess.Popen(
            ["npx", "vite", "--port", "5173", "--host", "0.0.0.0"],
            cwd=frontend_dir,
            shell=True,
            env=env,
        )
        processes.append(frontend)
        print(f"\n[AURA] Ready!")
        print(f"  Frontend:  http://localhost:5173")
        print(f"  Backend:   http://localhost:{args.port}")
        print(f"  API docs:  http://localhost:{args.port}/docs")
    else:
        print(f"\n[AURA] Ready!")
        print(f"  Backend:   http://localhost:{args.port}")
        print(f"  API docs:  http://localhost:{args.port}/docs")

    print(f"\n  Press Ctrl+C to stop.\n")

    def shutdown(sig, frame):
        print("\n[AURA] Shutting down...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for p in processes:
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Wait for any process to exit
    try:
        while True:
            for p in processes:
                retcode = p.poll()
                if retcode is not None:
                    print(f"[AURA] Process exited with code {retcode}")
                    shutdown(None, None)
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(None, None)


if __name__ == "__main__":
    main()

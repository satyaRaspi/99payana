"""Start Payana Screening Registration app locally.

This helper creates/uses a Python virtual environment for the backend,
installs missing backend requirements, installs missing frontend npm packages,
and starts both servers.

Fix in v1.2.1:
- Re-installs backend requirements if the virtual environment exists but uvicorn is missing.
- Re-installs frontend packages if node_modules exists but Vite is missing.
- Uses clearer error messages for Mac/Windows dependency issues.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = BACKEND / ".venv"
IS_WINDOWS = platform.system().lower().startswith("win")
PYTHON_BIN = VENV / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
NPM = "npm.cmd" if IS_WINDOWS else "npm"
VITE_BIN = FRONTEND / "node_modules" / ".bin" / ("vite.cmd" if IS_WINDOWS else "vite")


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("\n>", " ".join(map(str, cmd)))
    subprocess.check_call(cmd, cwd=str(cwd or ROOT))


def python_can_import(module_name: str) -> bool:
    if not PYTHON_BIN.exists():
        return False
    result = subprocess.run(
        [str(PYTHON_BIN), "-c", f"import {module_name}"],
        cwd=str(BACKEND),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def ensure_backend() -> None:
    if not PYTHON_BIN.exists():
        print("Creating backend Python virtual environment...")
        run([sys.executable, "-m", "venv", str(VENV)])

    # Always make sure pip is healthy. This is safe to run repeatedly.
    run([str(PYTHON_BIN), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], BACKEND)

    # Install requirements if uvicorn is absent, even if the venv already exists.
    if not python_can_import("uvicorn"):
        print("Backend dependency uvicorn is missing. Installing backend requirements...")
        run([str(PYTHON_BIN), "-m", "pip", "install", "-r", "requirements.txt"], BACKEND)
    else:
        print("Backend dependencies look good.")


def ensure_frontend() -> None:
    if not shutil.which(NPM):
        raise SystemExit(
            "Node.js/npm is not installed or not available in PATH. Install Node.js LTS and run this script again."
        )

    # node_modules can exist even when npm install failed midway; verify Vite specifically.
    if not VITE_BIN.exists():
        print("Frontend dependency Vite is missing. Installing frontend packages...")
        run([NPM, "install"], FRONTEND)
    else:
        print("Frontend dependencies look good.")



def is_port_busy(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0

def main() -> None:
    print("Starting Payana Screening Registration v1.2.9")
    try:
        ensure_backend()
        ensure_frontend()
        if is_port_busy(8000):
            print("\nPort 8000 is already in use. Stop the old backend first:")
            print("  lsof -i :8000")
            print("  kill -9 <PID>")
            raise SystemExit(1)
        if is_port_busy(5173):
            print("\nPort 5173 is already in use. Stop the old frontend first:")
            print("  lsof -i :5173")
            print("  kill -9 <PID>")
            raise SystemExit(1)
    except subprocess.CalledProcessError as exc:
        print("\nSetup failed while running:", " ".join(map(str, exc.cmd)))
        print("\nTry this clean reinstall from the project root:")
        print("  rm -rf backend/.venv frontend/node_modules")
        print("  python3 start_dev.py")
        raise SystemExit(exc.returncode)

    # Do not use uvicorn --reload by default because reload watchers can monitor backend/.venv
    # and repeatedly restart the server when site-packages files are touched.
    # Set PAYANA_BACKEND_RELOAD=1 if you specifically want live backend reload.
    import os
    backend_cmd = [
        str(PYTHON_BIN), "-m", "uvicorn", "main:app",
        "--host", "0.0.0.0", "--port", "8000",
    ]
    if os.environ.get("PAYANA_BACKEND_RELOAD") == "1":
        backend_cmd.extend([
            "--reload",
            "--reload-dir", str(BACKEND),
            "--reload-exclude", ".venv",
            "--reload-exclude", ".venv/*",
            "--reload-exclude", "__pycache__/*",
        ])
    frontend_cmd = [NPM, "run", "dev"]

    print("\nBackend:  http://localhost:8000/api/health")
    print("Frontend: http://localhost:5173")
    print("Default admin: admin / admin123\n")

    backend_proc = subprocess.Popen(backend_cmd, cwd=str(BACKEND))
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(FRONTEND))
    try:
        import time
        while True:
            backend_code = backend_proc.poll()
            frontend_code = frontend_proc.poll()
            if backend_code is not None:
                print(f"Backend stopped with exit code {backend_code}.")
                break
            if frontend_code is not None:
                print(f"Frontend stopped with exit code {frontend_code}.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
    finally:
        for proc in (backend_proc, frontend_proc):
            if proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    main()

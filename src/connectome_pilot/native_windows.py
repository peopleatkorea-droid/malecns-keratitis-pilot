"""MSVC build adapter; the upstream neural equations are left unchanged."""
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _compiler_environment(cache):
    if shutil.which("cl"):
        return os.environ.copy()
    base = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
    vswhere = base / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.exists():
        raise RuntimeError("Install MSVC C++ Build Tools or run from a Visual Studio developer shell")
    found = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
                            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
                            "-property", "installationPath"], check=True,
                           capture_output=True, text=True).stdout.strip()
    vcvars = Path(found) / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
    if not found or not vcvars.exists():
        raise RuntimeError("MSVC x64 C++ tools were not found")
    # The path comes from Microsoft's local installer registry, not a data manifest.
    script = cache / "compiler-environment.cmd"
    script.write_text(f'@echo off\ncall "{vcvars}" >nul\nif errorlevel 1 exit /b 1\nset\n',
                      encoding="utf-8")
    output = subprocess.run(["cmd.exe", "/d", "/c", str(script)], check=True,
                            capture_output=True, text=True, errors="replace").stdout
    env = os.environ.copy()
    for line in output.splitlines():
        if "=" in line and not line.startswith("="):
            key, value = line.split("=", 1)
            env[key.upper()] = value
    return env


def build_windows(cache=Path(".cache/native")):
    import flyocr.brain.native as native
    source = Path(native.__file__).with_name("kernel.cpp")
    source_hash = _digest(source)
    cache = Path(cache).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    binary = cache / (source_hash[:20] + "-" + platform.machine() + ".dll")
    manifest = binary.with_suffix(".dll.json")
    if binary.exists() and manifest.exists():
        saved = json.loads(manifest.read_text(encoding="utf-8"))
        if saved.get("source_sha256") == source_hash and saved.get("binary_sha256") == _digest(binary):
            return binary
    env = _compiler_environment(cache)
    compiler = shutil.which("cl", path=env.get("PATH"))
    if not compiler:
        raise RuntimeError("MSVC environment did not provide cl.exe")
    command = [compiler, "/nologo", "/O2", "/std:c++17", "/EHsc", "/LD", str(source),
               "/Fokernel.obj", "/link", "/OUT:" + str(binary),
               "/IMPLIB:kernel.lib", "/EXPORT:neural_advance"]
    subprocess.run(command, cwd=cache, env=env, check=True, capture_output=True,
                   text=True, errors="replace")
    manifest.write_text(json.dumps({"source_sha256": source_hash,
                                   "binary_sha256": _digest(binary),
                                   "compiler": "MSVC", "architecture": platform.machine()},
                                  indent=2), encoding="utf-8")
    return binary


def enable_windows_build():
    if sys.platform == "win32":
        import flyocr.brain.native as native
        native.build = build_windows

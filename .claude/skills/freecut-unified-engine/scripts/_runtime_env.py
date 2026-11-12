#!/usr/bin/env python3
"""
_runtime_env.py — Cross-Platform Runtime PATH & Vault Key Helper (v6.3)
=======================================================================
1. Automatically discovers newly installed binaries (`ffmpeg`, `ffprobe`, `node`, `npm`, `git`)
   across Windows (`WinGet\\Links`, `WinGet\\Packages`, live Registry `Path`), macOS Apple Silicon
   (`/opt/homebrew/bin`, `/usr/local/bin`), and Linux (`/usr/local/bin`, `/snap/bin`, `~/.local/bin`)
   so OpenBot never requires an app restart after first-run `winget` / `brew` installation.
2. Ensures Python user-site (`site.getusersitepackages()`) is importable when `pip install --user`
   was used on non-admin machines.
3. Supports `--vault-key <VAR_NAME> <VAULT_FILE_PATH>` (repeatable) across all CLI scripts, loading
   keys from OpenBot's encrypted vault files directly into process memory without printing values
   or writing secrets to `.env`.
"""
import glob
import os
import site
import sys

# Prevent Python from writing __pycache__/*.pyc inside .agents/skills/ so OpenBot Share stays clean ("installed")
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def ensure_user_site():
    try:
        user_site = site.getusersitepackages()
        if user_site and os.path.isdir(user_site) and user_site not in sys.path:
            sys.path.append(user_site)
    except Exception:
        pass


def ensure_runtime_paths():
    ensure_user_site()
    extra_dirs = []
    if os.name == "nt":
        local_app = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        if local_app:
            extra_dirs.append(os.path.join(local_app, "Microsoft", "WinGet", "Links"))
            for pattern in ("Gyan.FFmpeg*", "FFmpeg*", "BtbN.FFmpeg*", "OpenJS.NodeJS*", "Git.Git*"):
                for pkg_dir in glob.glob(os.path.join(local_app, "Microsoft", "WinGet", "Packages", pattern)):
                    for root_d, _, files_d in os.walk(pkg_dir):
                        low = {f.lower() for f in files_d}
                        if low & {"ffmpeg.exe", "ffprobe.exe", "node.exe", "git.exe"}:
                            extra_dirs.append(root_d)
            for py_scripts in glob.glob(os.path.join(local_app, "Programs", "Python", "Python*", "Scripts")):
                extra_dirs.append(py_scripts)
        if appdata:
            for py_scripts in glob.glob(os.path.join(appdata, "Python", "Python*", "Scripts")):
                extra_dirs.append(py_scripts)
        extra_dirs.extend(
            [
                r"C:\ffmpeg\bin",
                os.path.join(prog_files, "nodejs"),
                os.path.join(prog_files, "Git", "cmd"),
            ]
        )
        try:
            import winreg

            for hive, subkey in (
                (winreg.HKEY_CURRENT_USER, "Environment"),
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
            ):
                try:
                    with winreg.OpenKey(hive, subkey) as k:
                        val, _ = winreg.QueryValueEx(k, "Path")
                        if val:
                            extra_dirs.extend(os.path.expandvars(p.strip()) for p in val.split(";") if p.strip())
                except OSError:
                    pass
        except Exception:
            pass
    else:
        home = os.path.expanduser("~")
        extra_dirs.extend(
            [
                "/opt/homebrew/bin",
                "/opt/homebrew/sbin",
                "/usr/local/bin",
                "/usr/local/sbin",
                "/snap/bin",
                os.path.join(home, ".local", "bin"),
            ]
        )
        for py_bin in glob.glob(os.path.join(home, "Library", "Python", "3.*", "bin")):
            extra_dirs.append(py_bin)

    cur_path = os.environ.get("PATH", "")
    cur_set = {os.path.normcase(os.path.normpath(p)) for p in cur_path.split(os.pathsep) if p}
    to_add = []
    for d in extra_dirs:
        if d and os.path.isdir(d):
            norm = os.path.normcase(os.path.normpath(d))
            if norm not in cur_set:
                cur_set.add(norm)
                to_add.append(d)
    if to_add:
        os.environ["PATH"] = cur_path + (os.pathsep if cur_path else "") + os.pathsep.join(to_add)


def apply_vault_key_args():
    argv = sys.argv
    cleaned = [argv[0]]
    i = 1
    while i < len(argv):
        tok = argv[i]
        if tok == "--vault-key" and i + 2 < len(argv):
            var_name = argv[i + 1].strip()
            file_path = argv[i + 2].strip()
            if var_name and file_path and os.path.isfile(file_path):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                    secret_val = fh.read().strip()
                if secret_val:
                    os.environ[var_name] = secret_val
            i += 3
            continue
        cleaned.append(tok)
        i += 1
    sys.argv[:] = cleaned


def init():
    ensure_runtime_paths()
    apply_vault_key_args()

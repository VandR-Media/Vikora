"""Run AFTER Windows PyInstaller build to smoke-test the actual Vikora.exe.

Uses only a temporary directory and synthetic records. No actual resumes,
API keys, or personal files are touched. The executable is never exposed to
other computers: this test contacts 127.0.0.1 only.
"""
from __future__ import annotations

from contextlib import closing

import argparse
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid


def free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def fetch(url: str, *, host: str | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"Host": host} if host else {})
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, response.read(200_000)
    except urllib.error.HTTPError as err:
        return err.code, err.read(2048)


def exercise(exe: Path, data: Path, *, expected_candidate: str | None = None) -> None:
    port = free_local_port()
    env = os.environ.copy()
    env.update(VIKORA_DATA_DIR=str(data), VIKORA_DESKTOP_PORT=str(port), VIKORA_NO_BROWSER="1")
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    proc = subprocess.Popen([str(exe)], env=env, cwd=str(exe.parent),
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, creationflags=creation_flags)
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 75
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                raise AssertionError(f"Vikora.exe stopped during startup (exit={proc.returncode}). "
                                     f"See {data / 'vikora.log'}")
            try:
                status, _ = fetch(base + "/health")
                if status == 200:
                    break
            except (OSError, TimeoutError):
                pass
            time.sleep(0.35)
        else:
            raise AssertionError("Vikora.exe did not open its loopback endpoint within 75 seconds")

        status, page = fetch(base + "/app")
        assert status == 200 and b"Vikora" in page, "Browser interface missing from EXE"
        status, assets = fetch(base + "/assets/app.js")
        assert status == 200 and len(assets) > 1000, "Bundled JS file missing"
        status, _ = fetch(base + "/api/v1/me")
        assert status == 401, "Local API unexpectedly open without temporary token"
        status, _ = fetch(base + "/health", host="other-machine.invalid")
        assert status == 400, "Untrusted host was accepted"
        db_path = data / "vikora.sqlite3"
        assert db_path.is_file(), "Local SQLite database not created"
        with closing(sqlite3.connect(db_path, timeout=5)) as db, db:
            assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
            assert db.execute("select count(*) from user_accounts").fetchone()[0] >= 1
            if expected_candidate:
                assert db.execute("select count(*) from candidates where id = ?",
                                  (expected_candidate,)).fetchone()[0] == 1, "User data lost after upgrade/restart"
        print(f"PASS: Vikora.exe launched, UI loaded, API protected, database healthy (port {port})")
    finally:
        if proc.poll() is None:
            proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


def run_persistent_smoke(exe: Path, profile: Path) -> None:
    """Retain a synthetic record across successive installer executions.

    The profile path must be supplied by the Windows CI in RUNNER_TEMP;
    `windows_smoke.py` never deletes a caller-specified profile.
    """
    profile.mkdir(parents=True, exist_ok=True)
    marker = profile / "synthetic_smoke_id.txt"
    if marker.is_file():
        expected = marker.read_text(encoding="ascii").strip()
        if len(expected) != 32 or any(ch not in '0123456789abcdef' for ch in expected):
            raise AssertionError("Invalid smoke marker in the CI data folder")
        exercise(exe, profile, expected_candidate=expected)
        print("PASS: Installer upgrade preserved the previous synthetic candidate")
    else:
        exercise(exe, profile)
        candidate_id = uuid.uuid4().hex
        with closing(sqlite3.connect(profile / "vikora.sqlite3")) as db, db:
            db.execute("INSERT INTO candidates (id, full_name, source) VALUES (?, ?, ?)",
                       (candidate_id, "Synthetic Windows smoke candidate", "manual"))
            db.commit()
        marker.write_text(candidate_id, encoding="ascii")
        exercise(exe, profile, expected_candidate=candidate_id)
        print("PASS: New installation preserved the synthetic candidate after restart")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="Persistent test-only profile (used by isolated Windows CI)")
    args = parser.parse_args()
    exe = args.exe.resolve(strict=True)
    if args.data_dir is not None:
        run_persistent_smoke(exe, args.data_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="vikora-exe-smoke-") as name:
            run_persistent_smoke(exe, Path(name) / "profile")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"WINDOWS SMOKE FAILED: {exc}", file=sys.stderr)
        raise

"""Run the committed tests with no inherited credentials or outbound connections."""

import ctypes
import errno
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent / "harvey-baseline-check"
PYTHON = OUT / "venv/bin/python"


def run_parent():
    runtime = OUT / "runtime"
    runtime.mkdir(exist_ok=True)
    node_dir = Path(os.environ.get("CODEX_PRIMARY_RUNTIME_NODE", "/opt/codex/runtimes/codex-primary-runtime/dependencies/node/bin/node")).parent
    env = {
        "PATH": f"{OUT / 'venv/bin'}:{node_dir}:/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "TZ": "UTC",
        "TMPDIR": str(runtime),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_NO_INDEX": "1",
        "HARVEY_PACKAGE_TESTS": "1",
    }
    metadata = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "sha": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "status_before": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
        "environment_keys": sorted(env),
        "command": [str(PYTHON), str(Path(__file__).resolve()), "--child"],
        "pytest_arguments": ["-p", "pytest_asyncio.plugin", "tests", "-ra", "-q", "--junitxml", str(OUT / "pytest.xml"), "-o", f"cache_dir={OUT / 'pytest-cache'}"],
    }
    with (OUT / "versions.json").open("w") as f:
        subprocess.run([str(PYTHON), "-m", "pip", "list", "--format=json"], env=env, stdout=f, check=True)
    with (OUT / "pytest.log").open("w") as f:
        result = subprocess.run(metadata["command"], cwd=ROOT, env=env, stdout=f, stderr=subprocess.STDOUT)
    metadata.update({
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "exit_code": result.returncode,
        "status_after": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True),
    })
    (OUT / "run-metadata.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))
    print((OUT / "pytest.log").read_text()[-6000:])
    return result.returncode


def run_child():
    if platform.machine() != "x86_64" or sys.platform != "linux":
        raise RuntimeError("Network guard requires this verified Linux x86_64 runtime")

    class Filter(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]

    class Program(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]

    filters = (Filter * 4)(
        Filter(0x20, 0, 0, 0),
        Filter(0x15, 0, 1, 42),
        Filter(0x06, 0, 0, 0x00050000 | errno.EPERM),
        Filter(0x06, 0, 0, 0x7FFF0000),
    )
    program = Program(len(filters), filters)
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) or libc.prctl(22, 2, ctypes.byref(program)):
        raise OSError(ctypes.get_errno(), "Could not install inherited connect syscall guard")
    blocked = []

    def audit(event, args):
        if event == "socket.connect":
            blocked.append({"event": event})
            raise PermissionError("Baseline runner blocks socket connections")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = os.fsdecode(args[0])
            if path.startswith("/root/.codex/") and path.endswith(("auth.json", "/.env")) or path.startswith("/root/.claude/") and ("credential" in path or path.endswith("auth.json")):
                blocked.append({"event": "credential_file_read_blocked"})
                raise PermissionError("Baseline runner blocks real credential files")

    sys.addaudithook(audit)
    sys.path.insert(0, str(ROOT))
    import pytest
    args = ["-p", "pytest_asyncio.plugin", "tests", "-ra", "-q", "--junitxml", str(OUT / "pytest.xml"), "-o", f"cache_dir={OUT / 'pytest-cache'}"]
    class Evidence:
        def pytest_runtest_logreport(self, report):
            entry = {"nodeid": report.nodeid, "when": report.when, "outcome": report.outcome, "duration": report.duration}
            if report.failed or report.skipped:
                entry["detail"] = str(report.longrepr)
            with (OUT / "test-events.ndjson").open("a") as f:
                f.write(json.dumps(entry) + "\n")

    result = pytest.main(args, plugins=[Evidence()])
    (OUT / "isolation.json").write_text(json.dumps({
        "kernel_connect_guard": "installed; inherited by child processes",
        "python_network_and_credential_audit_guard": "installed",
        "blocked_attempts": blocked,
        "real_cli_tests": "not opted in; HARVEY_CODEX_CLI_TESTS absent",
        "packaging_test": "opted in; HARVEY_PACKAGE_TESTS=1; no-index wheel build",
    }, indent=2))
    return int(result)


if __name__ == "__main__":
    raise SystemExit(run_child() if "--child" in sys.argv else run_parent())

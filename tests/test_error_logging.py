import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


def is_coverage_enabled():
    # Detect if coverage is enabled in any way (coverage, subprocess, xdist, etc.)
    coverage_env_vars = [
        "COVERAGE_RUN",
        "COVERAGE_PROCESS_START",
        "PYTEST_XDIST_WORKER",
        "PYTEST_CURRENT_TEST",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
    ]
    return any(var in os.environ for var in coverage_env_vars)


@pytest.mark.skipif(
    is_coverage_enabled(),
    reason=(
        "Subprocess-based error logging test is incompatible with coverage/xdist. "
        "Skipped to prevent coverage data errors."
    ),
)
def test_error_log_file_created_on_crash():
    """
    Test that an error log file is created when main.py crashes.
    This test is skipped if coverage or xdist is enabled,
    as subprocess coverage data cannot be safely combined.
    """
    # Setup: ensure no pre-existing error log files
    log_dir = Path(".")
    for f in log_dir.glob("error_log_*.txt"):
        f.unlink()

    # Use subprocess to run main.py with env to trigger error and suppress GUI
    env = os.environ.copy()
    env["P21API_SUPPRESS_GUI"] = "1"
    env["P21API_TEST_TRIGGER_ERROR"] = "1"
    # Remove all known coverage env vars to avoid plugin errors in subprocess
    for var in [
        "COVERAGE_RUN",
        "COVERAGE_PROCESS_START",
        "PYTEST_XDIST_WORKER",
        "PYTEST_CURRENT_TEST",
        "COV_CORE_SOURCE",
        "COV_CORE_CONFIG",
        "COV_CORE_DATAFILE",
    ]:
        env.pop(var, None)

    result = subprocess.run(
        [sys.executable, "main.py"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    # Allow a moment for file system to sync
    time.sleep(0.5)

    # Check for error log file
    log_files = list(log_dir.glob("error_log_*.txt"))
    assert log_files, (
        f"No error log file found. Subprocess output: {result.stdout} {result.stderr}"
    )
    # Clean up
    for f in log_files:
        f.unlink()


def test_no_error_log_file_on_success():
    """
    Test that no error log file is created when main.py runs successfully.
    This test is always run, but subprocess coverage is stripped to avoid plugin errors.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        log_dir = tmp_path
        # Write a minimal valid .env file for main.py to run successfully
        env_file = tmp_path / "env"
        env_file.write_text(
            """
P21API_BASE_URL=https://example.com/odata
P21API_USERNAME=testuser
P21API_PASSWORD=testpass
P21API_START_DATE=2023-01-01
P21API_END_DATE=2023-01-02
P21API_REPORTS=daily_sales
P21API_SUPPRESS_GUI=1
""".strip()
        )
        # Remove any pre-existing error log files
        for f in log_dir.glob("error_log_*.txt"):
            f.unlink()

        env = os.environ.copy()
        env["P21API_SUPPRESS_GUI"] = "1"
        env["P21API_ENV_FILE"] = str(env_file)
        # Remove all known coverage env vars to avoid plugin errors in subprocess
        for var in [
            "COVERAGE_RUN",
            "COVERAGE_PROCESS_START",
            "PYTEST_XDIST_WORKER",
            "PYTEST_CURRENT_TEST",
            "COV_CORE_SOURCE",
            "COV_CORE_CONFIG",
            "COV_CORE_DATAFILE",
        ]:
            env.pop(var, None)

        subprocess.run(
            [sys.executable, "main.py"],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        time.sleep(0.5)
        log_files = list(log_dir.glob("error_log_*.txt"))
        assert not log_files, f"Unexpected error log file(s) found: {log_files}"

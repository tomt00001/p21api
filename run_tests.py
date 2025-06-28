"""Test script to run all tests with different configurations.

PYTEST EXECUTION METHODS:
This project supports multiple ways to run pytest:

1. uv run pytest (RECOMMENDED) - Uses project dependencies from pyproject.toml
   - Automatically manages virtual environment
   - Uses exact versions specified in dependency groups
   - No need to manually activate venv

2. python -m pytest - Requires manual venv activation or system-wide install
   - Must first: .venv\\Scripts\\Activate.ps1 (or source .venv/bin/activate on Unix)
   - Then: python -m pytest

3. Direct pytest command - If pytest is in PATH

For uv-managed projects like this one, 'uv run pytest' is preferred as it:
- Automatically uses the correct Python version and dependencies
- Doesn't require manual virtual environment activation
- Ensures consistent test environment across different machines
"""
# ruff: noqa: T201  # Allow print statements in this utility script

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and print the result."""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print("=" * 60)

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.stdout:
        print("STDOUT:")
        print(result.stdout)

    if result.stderr:
        print("STDERR:")
        print(result.stderr)

    print(f"Return code: {result.returncode}")
    return result.returncode == 0


def demonstrate_pytest_methods():
    """Demonstrate different ways to run pytest in this project."""
    print("Demonstrating pytest execution methods:\n")

    methods = [
        {
            "name": "uv run pytest (RECOMMENDED)",
            "command": ["uv", "run", "pytest", "--version"],
            "description": "Uses project dependencies, no venv activation needed",
        },
        {
            "name": "python -m pytest",
            "command": ["python", "-m", "pytest", "--version"],
            "description": "Requires venv activation or system install",
        },
        {
            "name": "direct pytest",
            "command": ["pytest", "--version"],
            "description": "If pytest is in PATH",
        },
    ]

    for method in methods:
        try:
            result = subprocess.run(
                method["command"], check=True, capture_output=True, text=True
            )
            status = f"✓ WORKS - {result.stdout.strip()}"
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            # Try to get more details about the failure
            if hasattr(e, "stderr") and e.stderr:
                status = f"✗ FAILED - {e.stderr.strip()}"
            elif hasattr(e, "stdout") and e.stdout:
                status = f"✗ FAILED - {e.stdout.strip()}"
            else:
                status = f"✗ FAILED - {str(e)}"

        print(f"{method['name']:<25}: {status}")
        print(f"{'':25}  {method['description']}")
        print()


def main():
    """Run comprehensive test suite."""
    # Change to project directory (where this script is located)
    project_dir = Path(__file__).parent
    os.chdir(project_dir)

    # Test configurations (will be updated with correct pytest command)
    test_configs_templates = [
        {
            "command": "{pytest_cmd} tests/ -v",
            "description": "Run all tests with verbose output",
        },
        {
            "command": "{pytest_cmd} tests/ -v --tb=short",
            "description": "Run all tests with short traceback",
        },
        {"command": "{pytest_cmd} tests/ -x", "description": "Stop on first failure"},
        {
            "command": "{pytest_cmd} tests/test_config.py -v",
            "description": "Run only config tests",
        },
        {
            "command": "{pytest_cmd} tests/test_odata_client.py -v",
            "description": "Run only OData client tests",
        },
        {
            "command": "{pytest_cmd} tests/test_reports.py -v",
            "description": "Run only report tests",
        },
        {
            "command": '{pytest_cmd} tests/ -m "not slow" -v',
            "description": "Run fast tests only",
        },
        {
            "command": '{pytest_cmd} tests/ -m "unit" -v',
            "description": "Run unit tests only",
        },
        {
            "command": "{pytest_cmd} tests/ --cov=p21api --cov=gui --cov-report=term",
            "description": "Run tests with coverage report",
        },
        {
            "command": "{pytest_cmd} tests/ --cov=p21api --cov=gui --cov-report=html",
            "description": "Generate HTML coverage report",
        },
        {
            "command": "{pytest_cmd} tests/ -n auto",
            "description": "Run tests in parallel",
        },
        {
            "command": (
                "{pytest_cmd} tests/ --ignore=tests/test_gui.py "
                "--cov=p21api --cov=gui --cov-report=term"
            ),
            "description": "Run tests with coverage (excluding GUI tests that crash)",
        },
        {
            "command": (
                "{pytest_cmd} tests/ --ignore=tests/test_gui.py "
                "--cov=p21api --cov=gui --cov-report=html"
            ),
            "description": "Generate HTML coverage report (excluding GUI tests)",
        },
    ]

    print("Starting comprehensive test suite...")
    print(f"Working directory: {os.getcwd()}")

    # Check if pytest is available (try uv run first, then uv tool, then regular pytest)
    pytest_cmd = None

    # Try uv run pytest (uses project dependencies - preferred)
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        pytest_cmd = "uv run pytest"
        print(f"Using uv run pytest: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Try uv tool run pytest (global tool)
    if not pytest_cmd:
        try:
            result = subprocess.run(
                ["uv", "tool", "run", "pytest", "--version"],
                check=True,
                capture_output=True,
                text=True,
            )
            pytest_cmd = "uv tool run pytest"
            print(f"Using uv tool run pytest: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    # Try regular pytest (if in PATH or venv activated)
    if not pytest_cmd:
        try:
            result = subprocess.run(
                ["pytest", "--version"], check=True, capture_output=True, text=True
            )
            pytest_cmd = "pytest"
            print(f"Using regular pytest: {result.stdout.strip()}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    if not pytest_cmd:
        print("ERROR: pytest is not installed or not available")
        print("Please install pytest using one of:")
        print("  - uv add --dev pytest (for project dependencies)")
        print("  - uv tool install pytest (for global tool)")
        print("  - pip install pytest (traditional method)")
        return False

    # Update test configurations with the correct pytest command
    test_configs = [
        {
            "command": config["command"].format(pytest_cmd=pytest_cmd),
            "description": config["description"],
        }
        for config in test_configs_templates
    ]

    results = []

    for config in test_configs:
        success = run_command(config["command"], config["description"])
        results.append((config["description"], success))

    # Summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print("=" * 60)

    for description, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status:4} - {description}")

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    print(
        f"\nTotal: {total_tests}, Passed: {passed_tests}, "
        f"Failed: {total_tests - passed_tests}"
    )

    if passed_tests == total_tests:
        print("\n🎉 All test configurations passed!")
        return True
    else:
        print(f"\n❌ {total_tests - passed_tests} test configuration(s) failed")
        return False


if __name__ == "__main__":
    # Add option to demonstrate pytest methods
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demonstrate_pytest_methods()
        sys.exit(0)

    success = main()
    sys.exit(0 if success else 1)

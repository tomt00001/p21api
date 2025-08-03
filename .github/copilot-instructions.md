## Tooling and MCP Server Guidance for AI Agents

- Use `uv` for all dependency management and Python command execution.
- Use `pytest` (via `test.ps1`) for all test runs.
- Use `ruff` for linting and formatting.
- Use `mypy` or `pyright` for type checking as specified in scripts.
- Use `PowerShell (.ps1)` scripts for all automation; only use `.bat` if absolutely necessary.
- Use `PyInstaller` for building Windows executables.
- Use `tempfile` and `pathlib` for all file and path operations in Python.
- If an MCP server is required, use the official Model Context Protocol server template for Python, ensure all endpoints and scripts are Windows-compatible, and document setup and usage in the repo.
- Document any new tools or server requirements in this file and in code comments.

# Copilot Instructions for p21api

## Project Overview

- **Purpose:** Extract and process data from P21 ERP systems via OData API, supporting automated, configurable report generation.
- **Key Features:**
  - Multiple report types (inventory, sales, invoices, consolidation)
  - Async/concurrent report execution
  - Robust error handling and structured logging
  - Both GUI (PyQt6) and CLI interfaces
  - Type safety (mypy/type hints)
  - High test coverage (pytest)

## Architecture & Key Components

- `main.py`: Entry point; dispatches to GUI or CLI based on environment/config.
- `p21api/`: Core business logic, OData client, and data processing modules.
- `gui/`: PyQt6-based GUI for configuration and report execution.
- `reports/`: Individual report implementations (see test structure for mapping).
- `tests/` & `tests/reports/`: Unit and integration tests, organized by report type.
- `env`, `env.sample`, `env.prod`: Environment variable files for configuration.

## Developer Workflows

- **Install dependencies:**
  - `uv sync` (recommended)
  - Or: `pip install -e .`
- **Run main app:**
  - CLI: `uv run python main.py`
  - GUI: `show_gui=True uv run python main.py`
- **Run tests:**
  - All: `uv run pytest -v` or `pytest tests/`
  - Specific: `pytest tests/reports/test_report_daily_sales.py`
- **Lint/Format:**
  - Lint: `uv run ruff check .`
  - Format: `uv run ruff format .`
- **Type check:**
  - `uv run mypy p21api`
- **Build executable:**
  - `./build.ps1` (Windows PowerShell)

## Project Conventions & Patterns

- **Configuration:**
  - Uses `.env`-style files; fallback to GUI for missing/invalid config.
- **Testing:**
  - Each report has a dedicated test file in `tests/reports/`.
  - Integration tests are also present for cross-report scenarios.
- **Error Handling:**
  - Centralized, with detailed logging and user feedback (see logging config in core modules).
- **Async:**
  - Reports may run concurrently for performance; see async patterns in report modules.
- **Type Safety:**
  - All core modules use type hints and are checked with mypy.

## Integration & External Dependencies

- **OData API:**
  - All data extraction is via P21 OData endpoints; see `p21api/` for client logic.
- **PyQt6:**
  - GUI is optional; can be toggled via environment variable.
- **PyInstaller:**
  - Used for building standalone executables (see `pyproject.toml` and `build.ps1`).

## Examples

- See `README.md` for sample environment files and usage.
- See `tests/reports/README.md` for test organization and running examples.

---

## Windows Platform Guidance for AI Agents

- All code, scripts, and paths must be Windows-compatible.
- Use `os.path.join`, `os.path.abspath`, or `pathlib.Path` for all file and directory operations—never hardcode path separators.
- Validate and sanitize all paths to prevent directory traversal vulnerabilities. Ensure all resolved paths remain within the intended workspace or output directories.
- Prefer PowerShell (`.ps1`) scripts for automation; only use batch (`.bat`) scripts if absolutely necessary. Do not generate Bash scripts.
- All test/build automation must work in PowerShell and not assume a Unix shell.
- Document any Windows-specific dependencies or behaviors in code comments and documentation.

---

**If you are an AI agent, follow these conventions and workflows to maximize productivity and maintain consistency with project standards.**

## Test Execution and Rerun Policy for AI Agents

- **Single Execution Principle:** Run the full test suite only once per relevant code change or patch, unless a failure or environment issue is detected.
- **Rerun Triggers:** Only rerun tests if:
  - The previous test run failed due to a transient/environmental error (e.g., timeout, resource lock, incomplete output).
  - The code under test has changed since the last run.
  - The user explicitly requests a rerun.
- **Output Validation:** Always capture and summarize test output. If a test fails, include the failure reason and root cause analysis in your documentation.
- **Efficiency:** Avoid redundant test runs. If a test passes and no relevant code has changed, do not rerun.
- **Documentation:** Log every test execution, including the reason for rerun (if applicable), to ensure traceability and minimize unnecessary cycles.

- **Test Runner Standard:** Always use the `test.ps1` script to execute tests unless explicitly instructed otherwise. This script ensures the correct environment, dependencies, and coverage reporting are applied. Do not invoke `pytest`, `uv run pytest`, or other test commands directly unless there is a documented exception.

**Example:**

> If a patch is applied to a report module, run the relevant tests once. If all tests pass, proceed. If a test fails due to a known transient error (e.g., network timeout), rerun only the affected test(s) once. If the same error recurs, document and escalate as needed.

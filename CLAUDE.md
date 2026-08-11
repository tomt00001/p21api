# CLAUDE.md

Guidance for Claude Code (and other AI agents) working in this repository.

## Project overview

p21api is a Windows-only Python CLI/GUI tool that extracts data from a P21 ERP
system via its OData API and writes it to CSV reports. It runs manually or on
a schedule (e.g. Task Scheduler) and is packaged as a standalone `.exe` via
PyInstaller for end users who don't have Python installed.

## Architecture

- `main.py` — entry point. Loads `Config`, optionally shows the GUI, opens an
  `ODataClient` as a context manager, then runs each configured report class
  **sequentially** in a loop, collecting exceptions. On an unhandled crash it
  writes a `p21api_error_<timestamp>.log` file capturing console output.
- `p21api/config.py` — `Config` (pydantic-settings `BaseSettings`), loaded from
  an `env` file. `Config.get_config_report_groups()` is the registry mapping a
  report-group name (e.g. `monthly`, `inventory`) to the list of report
  classes it runs; `report_groups` in the env file selects which groups run.
- `p21api/odata_client.py` — `ODataClient`: auth (bearer token), URL
  composition, pagination, automatic chunking of large OR-filters. Two query
  entry points: `query()` (GET) and `query_post()` (POST) — both return
  `(data, url)` or `data` respectively; prefer these over building requests
  by hand.
- `p21api/report_base.py` — `ReportBase` ABC. Every report implements
  `file_name_prefix` and `_run()`. Shared helpers: `build_or_filter()` (build
  an OData `field eq 'x' or field eq 'y'` filter from a set of values) and
  `_debug_dump(table, name_part)` (write an intermediate petl table to CSV
  only when `config.debug` is true — use this instead of a manual
  `if self._debug: etl.tocsv(...)` block).
- `p21api/report_invoice_base.py` — `InvoiceHeaderReportBase`: shared
  implementation for the three reports that export `p21_view_invoice_hdr`
  rows (`report_daily_sales.py`, `report_monthly_invoices.py`,
  `report_monthly_consolidation.py`). Subclasses just set `file_name_prefix`
  and optionally override `selects`/`filters`.
- Other `p21api/report_*.py` files follow a fetch → `build_or_filter` →
  fetch-related → `petl.join` → `cut` → `sort` → `tocsv` shape. When adding a
  new report in this family, reuse `ReportBase._debug_dump` for every
  intermediate table rather than re-adding the boilerplate.
- `gui/gui.py` — optional PyQt6 `DatePickerDialog`, shown when
  `config.should_show_gui` is true. It subclasses `QDialog` directly, so
  mocking `gui.gui.QDialog` in tests does **not** prevent real Qt
  construction — only mocking `gui.gui.DatePickerDialog` itself (as
  `show_gui_dialog` callers do) is safe headless. See `tests/test_gui.py`.
- `scripts/` — standalone dev tooling, not part of the shipped app:
  `fetch_odata_metadata.py` / `parse_odata_metadata.py` fetch and parse the
  OData `$metadata` XML into `odata_schema/odata_schema_summary.{md,json}`;
  `odata_schema_helper.py` provides a small Python API over that JSON for
  schema lookups (see README's "OData Schema for AI Agents" section).

## Developer workflow (Windows / PowerShell only)

This project assumes Windows + PowerShell. Don't write or suggest Bash
scripts, and don't assume a Unix shell — use `pathlib.Path` / `os.path.join`
for all paths, never hardcoded separators.

- Install deps: `uv sync` (add `--group dev` for dev tooling)
- Run the app: `uv run python main.py` (set `show_gui=true` in the env file,
  or `$env:SHOW_GUI='true'`, to launch the GUI)
- Run tests: `./test.ps1` (wraps `uv run pytest`; supports `-Coverage`,
  `-Fast`, `-Parallel`, `-TypeCheck`, `-FailFast`, and more — see the script)
- Lint: `uv run ruff check .` / format: `uv run ruff format .`
- Type check: `uv run mypy p21api`
- Build the Windows executable: `./build.ps1` (PyInstaller)
- Cut a release: `./release.ps1` (tags, opens a PR develop→main, creates a
  GitHub release, generates release notes listing the OData views used)

## Testing conventions

- Tests live in `tests/` (flat) and `tests/reports/` (one file per report
  class — see `tests/reports/README.md` for the rationale). All tests mock
  HTTP (`p21api.odata_client.requests`) — there is no live or recorded-cassette
  P21 integration testing; "integration" test files exercise multiple
  internal components together with mocked I/O, not a real server.
- The coverage gate (`pytest.ini`, `--cov-fail-under`) reflects measured
  reality, not an aspirational target — if you raise real coverage, raise the
  gate to match; don't lower it to paper over an untested change.
- When a report's `_run()` calls `petl.fromdicts`/`petl.aggregate`/etc.
  internally (not just once at the very end), tests must not globally mock
  `petl.fromdicts` — mock only `petl.tocsv` and inspect the table passed to
  it via `list(etl.dicts(mock_tocsv.call_args[0][0]))`. See
  `tests/reports/test_report_dead_inventory.py` for the pattern.

## Working with AI agents on this repo

Treat this like normal pair-programming: confirm before risky or hard-to-reverse
actions (force-push, history rewrite, deleting uncommitted work, etc.), and
don't skip that judgment even for a scoped or automated-sounding task.

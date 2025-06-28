#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run tests using uv run pytest with verbose output

.DESCRIPTION
    This script runs the test suite using uv run pytest with verbose output.
    It's a simple wrapper for quick test execution in uv-managed projects.

.PARAMETER Path
    Specific test path to run (defaults to tests/)

.PARAMETER Coverage
    Include coverage reporting

.PARAMETER Fast
    Run only fast tests (exclude slow marked tests)

.PARAMETER Parallel
    Run tests in parallel using pytest-xdist

.PARAMETER NoCov
    Disable coverage reporting (overrides pytest.ini settings)

.EXAMPLE
    .\test.ps1
    Run all tests with verbose output

.EXAMPLE
    .\test.ps1 -Coverage
    Run tests with coverage reporting

.EXAMPLE
    .\test.ps1 -Path "tests/test_config.py"
    Run specific test file

.EXAMPLE
    .\test.ps1 -Fast
    Run only fast tests

.EXAMPLE
    .\test.ps1 -NoCov
    Run tests without coverage reporting
#>

param(
    [string]$Path = "tests/",
    [switch]$Coverage,
    [switch]$Fast,
    [switch]$Parallel,
    [switch]$NoCov,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Running tests with uv..." -ForegroundColor Green
Write-Host "Working directory: $(Get-Location)" -ForegroundColor Gray

# Build pytest command
$pytest_args = @("run", "pytest", $Path, "-v")

if ($NoCov) {
    $pytest_args += @("--no-cov")
    Write-Host "Coverage reporting disabled" -ForegroundColor Yellow
} elseif ($Coverage) {
    $pytest_args += @("--cov=p21api", "--cov=gui", "--cov-report=term-missing", "--cov-report=html")
    Write-Host "Including coverage reporting" -ForegroundColor Yellow
}

if ($Fast) {
    $pytest_args += @("-m", "not slow")
    Write-Host "Running fast tests only" -ForegroundColor Yellow
}

if ($Parallel) {
    $pytest_args += @("-n", "auto")
    Write-Host "Running tests in parallel" -ForegroundColor Yellow
}

# Display command being run
Write-Host "Command: uv $($pytest_args -join ' ')" -ForegroundColor Cyan
Write-Host ("-" * 60) -ForegroundColor Gray

# Run the command
try {
    & uv $pytest_args
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`n✅ Tests completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Tests failed with exit code: $exitCode" -ForegroundColor Red
    }

    exit $exitCode
} catch {
    Write-Host "`n💥 Error running tests: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure uv is installed and the project dependencies are set up." -ForegroundColor Yellow
    Write-Host "Try running: uv sync" -ForegroundColor Yellow
    exit 1
}

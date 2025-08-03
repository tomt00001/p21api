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

.PARAMETER TypeCheck
    Pyright type checking before running tests

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

.EXAMPLE
    .\test.ps1 -TypeCheck
    Run tests without type checking
#>

param(
    [string]$Path = "tests/",
    [switch]$Coverage,
    [switch]$Fast,
    [switch]$Parallel,
    [switch]$NoCov,
    [switch]$TypeCheck,
    [ValidateSet('pyright','mypy')][string]$TypeChecker = 'pyright',
    [switch]$FailFast,
    [switch]$JUnitXml,
    [hashtable]$Env,
    [scriptblock]$PreHook,
    [scriptblock]$PostHook,
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


# Run pre-hook if provided
if ($PreHook) {
    Write-Host "Running pre-test hook..." -ForegroundColor Green
    & $PreHook
}

# Run type checking first (unless skipped)
if ($TypeCheck) {
    if ($TypeChecker -eq 'pyright') {
        Write-Host "Running type checking with pyright..." -ForegroundColor Green
        Write-Host "Command: uvx --with-requirements pyproject.toml pyright" -ForegroundColor Cyan
        Write-Host ("-" * 60) -ForegroundColor Gray
        try {
            & uvx --with-requirements pyproject.toml pyright
            $typeCheckExitCode = $LASTEXITCODE
            if ($typeCheckExitCode -eq 0) {
                Write-Host "✅ Type checking passed!" -ForegroundColor Green
            } else {
                Write-Host "❌ Type checking failed with exit code: $typeCheckExitCode" -ForegroundColor Red
                Write-Host "Fix type errors before running tests." -ForegroundColor Yellow
                exit $typeCheckExitCode
            }
        } catch {
            Write-Host "💥 Error running pyright: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "Make sure pyright is available via uvx." -ForegroundColor Yellow
            exit 1
        }
    } elseif ($TypeChecker -eq 'mypy') {
        Write-Host "Running type checking with mypy..." -ForegroundColor Green
        Write-Host "Command: uv run mypy p21api" -ForegroundColor Cyan
        Write-Host ("-" * 60) -ForegroundColor Gray
        try {
            & uv run mypy p21api
            $typeCheckExitCode = $LASTEXITCODE
            if ($typeCheckExitCode -eq 0) {
                Write-Host "✅ Type checking passed!" -ForegroundColor Green
            } else {
                Write-Host "❌ Type checking failed with exit code: $typeCheckExitCode" -ForegroundColor Red
                Write-Host "Fix type errors before running tests." -ForegroundColor Yellow
                exit $typeCheckExitCode
            }
        } catch {
            Write-Host "💥 Error running mypy: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "Make sure mypy is available via uv." -ForegroundColor Yellow
            exit 1
        }
    }
    Write-Host ("-" * 60) -ForegroundColor Gray
} else {
    Write-Host "⚠️  Type checking skipped" -ForegroundColor Yellow
}

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

if ($FailFast) {
    $pytest_args += @("--maxfail=1", "--exitfirst")
    Write-Host "Fail fast enabled" -ForegroundColor Yellow
}

if ($JUnitXml) {
    $pytest_args += @("--junitxml=test-results.xml")
    Write-Host "JUnit XML output enabled" -ForegroundColor Yellow
}

# Display command being run
Write-Host "Command: uv $($pytest_args -join ' ')" -ForegroundColor Cyan
Write-Host ("-" * 60) -ForegroundColor Gray

# Set environment variables if provided
if ($Env) {
    foreach ($key in $Env.Keys) {
        Write-Host "Setting environment variable: $key=$($Env[$key])" -ForegroundColor Gray
        Set-Item -Path "Env:$key" -Value $Env[$key]
    }
}

# Run the command
try {
    & uv $pytest_args
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "`n✅ Tests completed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Tests failed with exit code: $exitCode" -ForegroundColor Red
    }

    # Optionally print summary if JUnitXml was used
    if ($JUnitXml -and (Test-Path "test-results.xml")) {
        Write-Host "\nTest summary (from test-results.xml):" -ForegroundColor Cyan
        try {
            $xml = [xml](Get-Content "test-results.xml")
            $total = $xml.testsuite.tests
            $failures = $xml.testsuite.failures
            $errors = $xml.testsuite.errors
            $skipped = $xml.testsuite.skipped
            Write-Host "Total: $total, Failures: $failures, Errors: $errors, Skipped: $skipped" -ForegroundColor Cyan
        } catch {
            Write-Host "Could not parse test-results.xml for summary." -ForegroundColor Yellow
        }
    }

    # Run post-hook if provided
    if ($PostHook) {
        Write-Host "Running post-test hook..." -ForegroundColor Green
        & $PostHook
    }

    exit $exitCode
} catch {
    Write-Host "`n💥 Error running tests: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Make sure uv is installed and the project dependencies are set up." -ForegroundColor Yellow
    Write-Host "Try running: uv sync" -ForegroundColor Yellow
    exit 1
}

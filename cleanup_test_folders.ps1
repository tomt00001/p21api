#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Clean up test-generated folders

.DESCRIPTION
    This script removes all the test-generated output and test folders that were
    created by the performance tests. These folders were created because the Config
    class automatically creates directories when instantiated.

.PARAMETER DryRun
    Show what would be deleted without actually deleting

.PARAMETER Force
    Skip confirmation prompt

.EXAMPLE
    .\cleanup_test_folders.ps1
    Remove test folders with confirmation

.EXAMPLE
    .\cleanup_test_folders.ps1 -DryRun
    Show what would be deleted

.EXAMPLE
    .\cleanup_test_folders.ps1 -Force
    Remove folders without confirmation
#>

param(
    [switch]$DryRun,
    [switch]$Force
)

# Change to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Cleaning up test-generated folders..." -ForegroundColor Green

# Find all test-generated folders
$patterns = @("output*", "test*")
$excludePatterns = @("tests", "test.ps1", "test_output")  # Keep actual test directories and files

# Additional specific test-generated folders to clean up
$specificFolders = @(
    "test with spaces",
    "test-with-dashes",
    "test_with_underscores",
    "test.with.dots",
    "tëst_ôutput"
)

# Also find very long path folders
$veryLongPaths = Get-ChildItem -Directory | Where-Object { $_.Name -like "very_long_path_*" }

$foldersToDelete = @()

foreach ($pattern in $patterns) {
    $folders = Get-ChildItem -Directory -Name $pattern | Where-Object {
        $folder = $_
        # Exclude folders that should be kept
        $shouldExclude = $false
        foreach ($exclude in $excludePatterns) {
            if ($folder -eq $exclude) {
                $shouldExclude = $true
                break
            }
        }

        # Also exclude folders that don't match the numbered pattern
        if (!$shouldExclude -and $pattern -eq "output*") {
            $shouldExclude = $folder -notmatch "^output\d+$"
        }
        if (!$shouldExclude -and $pattern -eq "test*") {
            $shouldExclude = $folder -notmatch "^test\d+$"
        }

        return !$shouldExclude
    }

    $foldersToDelete += $folders
}

# Add specific test folders
foreach ($folder in $specificFolders) {
    if (Test-Path $folder -PathType Container) {
        $foldersToDelete += $folder
    }
}

# Add very long path folders
$foldersToDelete += $veryLongPaths.Name

if ($foldersToDelete.Count -eq 0) {
    Write-Host "No test-generated folders found to clean up." -ForegroundColor Yellow
    exit 0
}

Write-Host "Found $($foldersToDelete.Count) test-generated folders:" -ForegroundColor Cyan

# Show first 10 and last 10 if there are many
if ($foldersToDelete.Count -le 20) {
    $foldersToDelete | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    $foldersToDelete[0..9] | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    Write-Host "  ... $($foldersToDelete.Count - 20) more folders ..." -ForegroundColor Gray
    $foldersToDelete[-10..-1] | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

if ($DryRun) {
    Write-Host "`nDRY RUN: Would delete $($foldersToDelete.Count) folders" -ForegroundColor Yellow
    exit 0
}

# Confirm deletion unless Force is specified
if (!$Force) {
    $response = Read-Host "`nDelete these $($foldersToDelete.Count) folders? (y/N)"
    if ($response -notmatch "^[Yy]") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# Delete folders
$deleted = 0
$errors = 0

Write-Host "`nDeleting folders..." -ForegroundColor Green

foreach ($folder in $foldersToDelete) {
    try {
        Remove-Item -Path $folder -Recurse -Force
        $deleted++
        if ($deleted % 100 -eq 0) {
            Write-Host "Deleted $deleted folders..." -ForegroundColor Gray
        }
    } catch {
        Write-Host "Error deleting $folder : $($_.Exception.Message)" -ForegroundColor Red
        $errors++
    }
}

Write-Host "`n✅ Cleanup complete!" -ForegroundColor Green
Write-Host "Deleted: $deleted folders" -ForegroundColor Green
if ($errors -gt 0) {
    Write-Host "Errors: $errors folders" -ForegroundColor Red
}

# Show remaining folders for verification
$remainingTestFolders = Get-ChildItem -Directory | Where-Object { $_.Name -match "^(output|test)\d+$" }
if ($remainingTestFolders.Count -gt 0) {
    Write-Host "`n⚠️  Still found $($remainingTestFolders.Count) numbered folders" -ForegroundColor Yellow
} else {
    Write-Host "`n🎉 All test-generated folders cleaned up!" -ForegroundColor Green
}

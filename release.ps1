


# Usage:
#   ./release.ps1
#   ./release.ps1 -ArtifactPath "my.exe"
#   ./release.ps1 -Release
#   ./release.ps1 -ArtifactPath "my.exe" -Release

param(
    [string]$ArtifactPath = "dist/P21 Data Exporter.exe",
    [switch]$Release
)


Set-StrictMode -Version Latest

if ($Release) {
    git checkout main
    git pull origin main

    # Checkout the develop branch and ensure it's up to date
    git checkout develop
    git pull origin develop

    # Create a pull request from develop to main
    gh pr create --base main --head develop --title "Merge develop into main" --body "Automated PR to merge latest changes from develop into main"

    # Wait for the PR to be available before proceeding
    Write-Host "[INFO] Waiting for PR to be ready..."
    Start-Sleep -Seconds 5

    # Get the PR number
    $pr_number = gh pr list --base main --head develop --state open --json number --jq '.[0].number'

    if ($pr_number) {
        Write-Host "[INFO] Merging PR #$pr_number"

        # Merge the pull request
        gh pr merge $pr_number --merge

        # Checkout main and pull latest changes
        git checkout main
        git pull origin main
    } else {
        Write-Host "[INFO] No open PR found. Please check manually."
    }
}

Write-Host "[INFO] Do you want to run build first? (yes/no)"
$confirmation = Read-Host
if ($confirmation -ne "yes") {
    Write-Host "[INFO] Build skipped by user."
} else {
    Write-Host "[INFO] Running build script..."
    .\build.ps1
}



# --- Main Release Logic ---

# Generate a date-based tag
$newTag = "version-$(Get-Date -Format yyyyMMdd)"

if ($Release) {
    git tag $newTag
    git push origin $newTag
}

$releaseTitle = "Release $newTag"
$releaseDate = Get-Date -Format yyyy-MM-dd

# --- Extract OData views used in all reports ---
$reportDir = Join-Path $PSScriptRoot 'p21api'
$reportFiles = Get-ChildItem -Path $reportDir -Recurse -Include 'report_*.py' -File
# Use a more robust regex to match OData view names (e.g., p21_view_*, p21_*_view)
$viewPattern = '(?<![\w])p21_[a-zA-Z0-9_]*view[a-zA-Z0-9_]*'
$allViews = @()
foreach ($file in $reportFiles) {
    $matches = Select-String -Path $file.FullName -Pattern $viewPattern -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value }
    $allViews += $matches
}
$uniqueViews = $allViews | Sort-Object -Unique | Sort-Object
$viewsText = "`n`n## OData Views Used in This Release`n"
if ($uniqueViews.Count -gt 0) {
    $viewsText += ($uniqueViews | ForEach-Object { "- $_" } | Out-String)
} else {
    $viewsText += "_None found_`n"
}

# --- Compose Release Notes ---
$releaseNotes = @()
$releaseNotes += "## Summary"
$releaseNotes += "- Release Date: $releaseDate"
$releaseNotes += "- Tag: $newTag"
$releaseNotes += "- Artifact: $ArtifactPath"
$releaseNotes += ""
$releaseNotes += "Release created on $releaseDate."
$releaseNotes += $viewsText
$releaseNotes = $releaseNotes -join "`n"

if ($Release) {
    Write-Host "[INFO] Tag: $newTag"
    Write-Host "[INFO] Artifact Path: $ArtifactPath"
    Write-Host "[INFO] Release Title: $releaseTitle"
    Write-Host "[INFO] Release Notes:`n$releaseNotes"
    if (Test-Path $ArtifactPath) {
        # Use splatting to ensure correct argument expansion and quoting
        $ghArgs = @(
            $newTag,
            $ArtifactPath,
            "--title", $releaseTitle,
            "--notes", $releaseNotes,
            "--prerelease"
        )
        $ghResult = gh release create @ghArgs 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[INFO] Release $newTag created successfully!"
            # Open the GitHub release page in the default browser
            $repoUrl = "https://github.com/tomt00001/p21api"
            $releaseUrl = "$repoUrl/releases/tag/$newTag"
            Write-Host "[INFO] Opening release page: $releaseUrl"
            Start-Process $releaseUrl
        } else {
            Write-Host "[ERROR] gh release create failed. Output: $ghResult"
            exit 1
        }
    } else {
        Write-Host "[ERROR] Artifact not found at $ArtifactPath. Build may have failed or was skipped. Release not created."
        exit 1
    }
} else {
    Write-Host "[DRYRUN] Tag: $newTag"
    Write-Host "[DRYRUN] Artifact Path: $ArtifactPath"
    Write-Host "[DRYRUN] Release Title: $releaseTitle"
    Write-Host "[DRYRUN] Release Notes:`n$releaseNotes"
    Write-Host "[DRYRUN] No tag, push, or GitHub release was created."
}

if ($Release) {
    git pull origin main
    git checkout develop
    git pull origin develop
}

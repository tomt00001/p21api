# Ensure we are on the main branch and up to date
git checkout main
git pull origin main

# Checkout the develop branch and ensure it's up to date
git checkout develop
git pull origin develop

# Create a pull request from develop to main
gh pr create --base main --head develop --title "Merge develop into main" --body "Automated PR to merge latest changes from develop into main"

# Wait for the PR to be available before proceeding
Write-Output "Waiting for PR to be ready..."
Start-Sleep -Seconds 5

# Get the PR number
$pr_number = gh pr list --base main --head develop --state open --json number --jq '.[0].number'

if ($pr_number) {
    Write-Output "Merging PR #$pr_number"
    
    # Merge the pull request
    gh pr merge $pr_number --merge --delete-branch

    # Checkout main and pull latest changes
    git checkout main
    git pull origin main
} else {
    Write-Output "No open PR found. Please check manually."
}

# # Ask for confirmation before running build
# $confirmation = Read-Host "Do you want to run build first? (yes/no)"

# if ($confirmation -eq "yes") {
#     # Run the build script
#     .\build.ps1
# }

# Ask for confirmation before switching to the main branch
# $confirmation = Read-Host "Do you want to switch to the 'main' branch and proceed with the release? (yes/no)"

# if ($confirmation -eq "yes") {
#     # Generate a date-based tag
#     $newTag = "version-$(Get-Date -Format yyyyMMdd)"
#     git tag $newTag
#     git push origin $newTag

#     # Paths to your files
#     $filePaths = @("dist/P21 Data Exporter.exe")

#     # Create a release with the new tag
#     gh release create $newTag $filePaths --title "Release $newTag" --notes "Release created on $(Get-Date -Format yyyy-MM-dd)" --prerelease

#     Write-Host "Release $newTag created successfully!"
# } else {
#     Write-Host "Release creation aborted."
# }

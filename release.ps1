# Ask for confirmation before switching to the main branch
$confirmation = Read-Host "Do you want to switch to the 'main' branch and proceed with the release? (yes/no)"

if ($confirmation -eq "yes") {
    # Make sure main is up to date before creating a new release
    # TODO this probably needs to merge or creata pull request
    git checkout main
    git pull origin main

    # Generate a date-based tag
    $newTag = "version-$(Get-Date -Format yyyyMMdd)"
    git tag $newTag
    git push origin $newTag

    # Paths to your files
    $filePaths = @("dist/P21 Data Exporter.exe")

    # Create a release with the new tag
    gh release create $newTag $filePaths --title "Release $newTag" --notes "Release created on $(Get-Date -Format yyyy-MM-dd)" --prerelease

    Write-Host "Release $newTag created successfully!"
} else {
    Write-Host "Release creation aborted."
}

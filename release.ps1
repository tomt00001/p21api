# Generate a date-based tag
$newTag = "version-$(Get-Date -Format yyyyMMdd)"
git tag $newTag
git push origin $newTag

$filePaths = @("dist/P21 Data Exporter.exe", "dist/.env")

# Create a release with the new tag
gh release create $newTag $filePaths --title "Release $newTag" --notes "Release created on $(Get-Date -Format yyyy-MM-dd)" --prerelease

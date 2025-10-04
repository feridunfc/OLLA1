param(
  [string]$RepoName = "multi-ai-local-v42",
  [string]$Remote = "origin",
  [string]$GitHubUrl = ""
)
if (-not (Test-Path .git)) { git init }
git add .
git commit -m "chore: bootstrap v4.2 local secure upgrade"
if ($GitHubUrl -ne "") {
  git remote remove $Remote 2>$null
  git remote add $Remote $GitHubUrl
  git branch -M main
  git push -u $Remote main
  Write-Host "✅ pushed to $GitHubUrl"
} else {
  Write-Host "ℹ️  Remote URL verilmedi. 'scripts/github_init.ps1 -GitHubUrl https://github.com/<user>/<repo>.git'"
}

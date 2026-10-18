# One-line setup for the CSAI Leak Guard game (Windows). Paste into PowerShell:
#
#   powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/shreev2703/csai-leak-guard/main/install.ps1 | iex"
#
# It installs uv (which installs Python for you), downloads the game into
# C:\Users\<you>\csai-leak-guard, and starts it. Paste the same line again to restart.
# It never overwrites your filter.py.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$GithubUser = "shreev2703"
$RepoZip = if ($env:LEAKGUARD_ZIP) { $env:LEAKGUARD_ZIP } else { "https://github.com/$GithubUser/csai-leak-guard/archive/refs/heads/main.zip" }
$Dest = Join-Path $HOME "csai-leak-guard"
$env:Path = "$HOME\.local\bin;$env:Path"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "==> Installing uv (one time, about 10 seconds)..."
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  $env:Path = "$HOME\.local\bin;$env:Path"
}

if (Test-Path (Join-Path $Dest "leakguard.py")) {
  Write-Host "==> Found the game in $Dest (keeping your changes)"
} else {
  Write-Host "==> Downloading the game into $Dest ..."
  $Tmp = Join-Path ([IO.Path]::GetTempPath()) ("csai-lg-" + [Guid]::NewGuid())
  New-Item -ItemType Directory $Tmp | Out-Null
  Invoke-WebRequest $RepoZip -OutFile "$Tmp\game.zip" -UseBasicParsing
  Expand-Archive "$Tmp\game.zip" -DestinationPath "$Tmp\x"
  $Inner = Get-ChildItem "$Tmp\x" -Directory | Select-Object -First 1
  New-Item -ItemType Directory -Force $Dest | Out-Null
  Copy-Item -Recurse -Force (Join-Path $Inner.FullName "*") $Dest
  Remove-Item -Recurse -Force $Tmp
}

Set-Location $Dest
Write-Host "==> Starting Leak Guard. Your browser will open in a moment."
Write-Host "    (If it doesn't, open the link printed below.)"
if ($env:CI) { uv run leakguard.py --check } else { uv run leakguard.py }

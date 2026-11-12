<#
.SYNOPSIS
  FreeCut Universal Studio Bot (v6) — One-Command Windows Installer (`install.ps1`)
.DESCRIPTION
  Installs & verifies everything needed on a fresh Windows PC:
    1. Python 3.11+, FFmpeg, Node.js LTS, and Git via `winget` (if missing)
    2. Python packages (`faster-whisper`, `edge-tts`, `rembg`, `playwright`, `rapidocr-onnxruntime`, `yt-dlp`)
    3. Headless Playwright Chromium browser (for 30fps Motion Graphics & Web Press Clippings)
    4. Mirrors `.agents/skills` -> `.claude/skills` so Gemini/Antigravity, Claude Code, Codex/Cursor, and OpenBot all load the skills automatically
    5. Optional `-InstallFreeCutApp` flag clones and sets up `walterlow/freecut` locally (`start-freecut.ps1`)
#>
param(
    [switch]$InstallFreeCutApp = $false,
    [switch]$UseVenv = $false,
    [switch]$SetupKeys = $false
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " FreeCut Universal Studio Bot v6 — Windows Automatic Setup" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

function Ensure-WingetTool {
    param([string]$Cmd, [string]$WingetId, [string]$Label)
    $found = Get-Command $Cmd -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
    if ($found) {
        Write-Host "  [OK] $Label found: $($found.Source)" -ForegroundColor Green
        return
    }
    Write-Host "  [INSTALL] $Label missing -> installing via winget ($WingetId)..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "$Label is not installed and 'winget' is unavailable. Please install $Label manually."
    }
    winget install --id $WingetId -e --accept-package-agreements --accept-source-agreements
    # Refresh PATH for current session (including WinGet\Links and newly installed Python/Node/Git)
    $wgLinks = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User") + ";" + $wgLinks
}

Write-Host "`n[1/5] Checking System Binaries (Python, FFmpeg, Node.js, Git)..." -ForegroundColor Cyan
Ensure-WingetTool -Cmd "python" -WingetId "Python.Python.3.12" -Label "Python 3"
Ensure-WingetTool -Cmd "ffmpeg" -WingetId "Gyan.FFmpeg" -Label "FFmpeg"
Ensure-WingetTool -Cmd "node"   -WingetId "OpenJS.NodeJS.LTS" -Label "Node.js LTS"
Ensure-WingetTool -Cmd "git"    -WingetId "Git.Git" -Label "Git"

$PyExe = "python"
if ($UseVenv) {
    Write-Host "`n[2/5] Creating isolated virtual environment (.venv)..." -ForegroundColor Cyan
    if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) {
        python -m venv "$Root\.venv"
    }
    $PyExe = "$Root\.venv\Scripts\python.exe"
} else {
    Write-Host "`n[2/5] Using system Python ($((Get-Command python).Source))..." -ForegroundColor Cyan
}

Write-Host "  Installing Python packages from requirements.txt..." -ForegroundColor Yellow
& $PyExe -B -m pip install --upgrade pip
& $PyExe -B -m pip install -r "$Root\requirements.txt"

Write-Host "`n[3/5] Installing Playwright Chromium headless renderer..." -ForegroundColor Cyan
& $PyExe -B -m playwright install chromium

Write-Host "`n[4/5] Syncing skills for all Frontier AIs (.agents/skills <-> .claude/skills)..." -ForegroundColor Cyan
$ClaudeSkills = Join-Path $Root ".claude\skills"
if (Test-Path $ClaudeSkills) { Remove-Item -Recurse -Force $ClaudeSkills }
New-Item -ItemType Directory -Force -Path $ClaudeSkills | Out-Null
foreach ($sk in "doc-art-director","doc-lottie-overlays","doc-motion-scenes","freecut-unified-engine") {
    $srcSk = Join-Path $Root ".agents\skills\$sk"
    if (Test-Path $srcSk) {
        Copy-Item -Recurse -Force $srcSk (Join-Path $ClaudeSkills $sk)
        Remove-Item -Force (Join-Path $ClaudeSkills "$sk\.openbot-managed.json") -ErrorAction SilentlyContinue
    }
}

if (-not (Test-Path "$Root\.env") -and (Test-Path "$Root\.env.example")) {
    Copy-Item "$Root\.env.example" "$Root\.env"
    Write-Host "  [OK] Created .env from .env.example (0 mandatory keys needed)." -ForegroundColor Green
}

if ($InstallFreeCutApp) {
    Write-Host "`n[Optional] Cloning & installing local FreeCut Web Editor (walterlow/freecut)..." -ForegroundColor Cyan
    $FcDir = Join-Path $Root "freecut-app"
    if (-not (Test-Path $FcDir)) {
        git clone --depth 1 https://github.com/walterlow/freecut.git $FcDir
    }
    Push-Location $FcDir
    npm install
    Pop-Location
    @"
Set-Location "$FcDir"
npm run dev
"@ | Set-Content -Encoding UTF8 (Join-Path $Root "start-freecut.ps1")
    Write-Host "  [OK] FreeCut app installed! Run .\start-freecut.ps1 anytime to open in browser." -ForegroundColor Green
}

Write-Host "`n[5/5] Running Environment Doctor Verification..." -ForegroundColor Cyan
& $PyExe -B "$Root\doctor.py"

if ($SetupKeys) {
    & $PyExe -B "$Root\.agents\skills\freecut-unified-engine\scripts\bootstrap_env.py" --setup-keys
} else {
    Write-Host "`n[TIP] 0 API keys required! Want to add your FREE Pixabay HD key (pixabay.com/api/docs/) or optional Groq/ElevenLabs keys?" -ForegroundColor Green
    Write-Host "      Run: python -B .agents\skills\freecut-unified-engine\scripts\bootstrap_env.py --setup-keys" -ForegroundColor Gray
}

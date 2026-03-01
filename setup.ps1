# Setup script for Windows PowerShell.
# For macOS/Linux, use setup.sh instead.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Prefer Python 3.11 or 3.12 (good wheel support). Fall back to python/python3.
$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($ver in @("3.11", "3.12", "3.13")) {
        $out = & py -$ver -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) {
            $python = "py", "-$ver"
            break
        }
    }
}
if (-not $python) {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $exe = (Get-Command python).Source
        if ($exe -notmatch "WindowsApps") { $python = "python" }
    }
}
if (-not $python) {
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $exe = (Get-Command python3).Source
        if ($exe -notmatch "WindowsApps") { $python = "python3" }
    }
}
if (-not $python) {
    Write-Error "Python 3.11+ not found. Install from python.org and avoid the Windows Store alias."
    exit 1
}

if ($python -is [array]) {
    & $python[0] $python[1..($python.Length-1)] setup.py
} else {
    & $python setup.py
}

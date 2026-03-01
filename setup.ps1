# Setup script for Windows PowerShell.
# For macOS/Linux, use setup.sh instead.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Use python or python3, whichever is available
$python = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $python = "python3"
} else {
    Write-Error "python or python3 not found. Please install Python 3.11+ first."
    exit 1
}

& $python setup.py

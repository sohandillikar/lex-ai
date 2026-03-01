#!/usr/bin/env bash
# Setup script for macOS and Linux (also works in Git Bash and WSL on Windows).
# For native Windows PowerShell, use setup.ps1 instead.
set -e

cd "$(dirname "$0")"

# Use python3 or python, whichever is available
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "Error: python3 or python not found. Please install Python 3.11+ first."
    exit 1
fi

exec "$PYTHON" setup.py

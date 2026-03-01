#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.11+ first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "Error: docker not found. Please install Docker first."
    exit 1
fi

if [ ! -f .env ]; then
    echo "Error: .env file not found. Copy .env.example to .env and fill in your values."
    exit 1
fi

echo "Starting PostgreSQL + pgvector..."
docker compose up -d

echo "Installing dependencies..."
pip3 install -q -r requirements.txt

echo "Setting up MCP server..."
python3 -m src.init

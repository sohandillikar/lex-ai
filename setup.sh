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
    cp .env.example .env
    echo "Created .env from .env.example. Please edit .env and add your OpenAI API key."
fi

echo "Starting PostgreSQL + pgvector..."
docker compose up -d

echo "Installing dependencies..."
pip3 install -q -r requirements.txt

echo "Installing Playwright browsers for Crawl4AI..."
crawl4ai-setup

echo "Waiting for PostgreSQL to be ready..."
until docker compose exec -T postgres pg_isready -U postgres 2>/dev/null; do
    sleep 2
done

echo "Setting up MCP server..."
python3 -m src.init

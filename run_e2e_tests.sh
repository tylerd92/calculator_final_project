#!/bin/bash

# Script to run Playwright end-to-end tests

set -e  # Exit on any error

echo "Setting up environment for Playwright E2E tests..."

# Change to project directory
cd /home/tyler/is601/module13_assignment

# Use the virtual environment python
PYTHON_CMD="/home/tyler/is601/module13_assignment/venv/bin/python"

# Install Playwright browsers if not already installed
echo "Installing Playwright browsers..."
$PYTHON_CMD -m playwright install

# Create test results directory
mkdir -p test-results/videos
mkdir -p test-results/screenshots

echo "Running Playwright E2E tests..."

# Run the e2e tests with proper environment variables
HEADLESS=true \
BASE_URL=http://localhost:8000 \
$PYTHON_CMD -m pytest tests/e2e/test_playwright_simple.py -v -s --tb=short

echo "E2E tests completed!"

#!/bin/bash

# Render startup script
set -e

echo "🚀 Starting Calculator API on Render..."

# Initialize database tables
echo "📊 Initializing database..."
python -m app.database_init

# Start the FastAPI application
echo "🌐 Starting web server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1

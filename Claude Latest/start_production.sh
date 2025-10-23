#!/bin/bash

# Production Startup Script for Kebabalab VAPI Server
# Usage: ./start_production.sh

set -e

echo "=========================================="
echo "Kebabalab VAPI Server - Production"
echo "=========================================="
echo ""

# Check if running as root (not recommended)
if [ "$EUID" -eq 0 ]; then
    echo "WARNING: Running as root is not recommended"
    echo "Consider creating a dedicated user for the application"
    echo ""
fi

# Load environment
if [ -f .env.production ]; then
    echo "Loading production environment..."
    export $(cat .env.production | grep -v '^#' | xargs)
else
    echo "ERROR: .env.production file not found"
    echo "Please create it from .env.production.example"
    exit 1
fi

# Set default port
PORT=${PORT:-8000}

# Create necessary directories
echo "Creating directories..."
mkdir -p logs
mkdir -p data
mkdir -p backups

# Check if database exists, create if not
if [ ! -f data/orders.db ]; then
    echo "Database not found, will be created on first run"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Check dependencies
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null || {
    echo "ERROR: Flask not installed"
    echo "Run: pip install -r requirements.txt"
    exit 1
}

echo "✓ Dependencies OK"
echo ""

# Kill any existing instances
echo "Checking for existing server instances..."
pkill -f server_simplified.py 2>/dev/null && echo "✓ Stopped old instance" || echo "✓ No existing instances"
echo ""

# Backup database before starting
if [ -f data/orders.db ]; then
    BACKUP_FILE="backups/orders.db.backup-$(date +%Y%m%d-%H%M%S)"
    echo "Creating database backup: $BACKUP_FILE"
    cp data/orders.db "$BACKUP_FILE"
    echo "✓ Backup created"
    echo ""
fi

# Display configuration
echo "=========================================="
echo "Configuration:"
echo "=========================================="
echo "Environment: ${ENVIRONMENT:-production}"
echo "Port: $PORT"
echo "Log Level: ${LOG_LEVEL:-INFO}"
echo "Log File: ${LOG_FILE:-logs/kebabalab_production.log}"
echo "=========================================="
echo ""

# Ask for confirmation
read -p "Start server? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "Starting server..."
echo ""

# Choose how to run
if command -v gunicorn &> /dev/null; then
    echo "Using Gunicorn (production-grade)..."
    # Run with gunicorn for production
    gunicorn \
        -w 4 \
        -b 0.0.0.0:$PORT \
        --timeout 120 \
        --log-level ${LOG_LEVEL:-info} \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --capture-output \
        --enable-stdio-inheritance \
        server_simplified:app
else
    echo "Gunicorn not found, using Flask development server"
    echo "For production, install gunicorn: pip install gunicorn"
    echo ""
    # Fallback to Flask development server
    python3 server_simplified.py
fi

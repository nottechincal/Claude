#!/bin/bash
# ======================================
# Stuffed Lamb Server - Linux/Mac Startup Script
# ======================================

set -e  # Exit on error

echo ""
echo "===================================="
echo "Stuffed Lamb VAPI Ordering System"
echo "Starting server..."
echo "===================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo ""
    echo "Please create .env file:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Edit .env with your Twilio credentials"
    echo "  3. Update SHOP_ORDER_TO with shop phone number"
    echo ""
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "[INFO] Activating virtual environment..."
    source venv/bin/activate
else
    echo "[WARNING] Virtual environment not found at venv/"
    echo "[INFO] Using system Python..."
fi

# Install/update dependencies
echo "[INFO] Checking dependencies..."
pip install -r requirements.txt --quiet || {
    echo "[ERROR] Failed to install dependencies"
    exit 1
}

# Run the server
echo ""
echo "[INFO] Starting Stuffed Lamb server..."
echo "[INFO] Press Ctrl+C to stop"
echo ""
python3 run.py

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate 2>/dev/null || true
fi

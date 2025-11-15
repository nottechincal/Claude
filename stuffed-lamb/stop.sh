#!/bin/bash
# ======================================
# Stuffed Lamb - Stop All Services (Linux/Mac)
# ======================================

echo ""
echo "===================================="
echo "Stopping Stuffed Lamb Services"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop server
if [ -f /tmp/stuffed-lamb.pid ]; then
    SERVER_PID=$(cat /tmp/stuffed-lamb.pid)
    echo -e "${GREEN}[INFO] Stopping Stuffed Lamb server (PID: $SERVER_PID)...${NC}"
    kill $SERVER_PID 2>/dev/null || echo -e "${YELLOW}[WARNING] Server process not found${NC}"
    rm /tmp/stuffed-lamb.pid
else
    echo -e "${YELLOW}[INFO] Server PID file not found, trying by process name...${NC}"
    pkill -f "python.*run.py" || echo -e "${YELLOW}[WARNING] No server process found${NC}"
fi

# Stop ngrok
if [ -f /tmp/stuffed-lamb-ngrok.pid ]; then
    NGROK_PID=$(cat /tmp/stuffed-lamb-ngrok.pid)
    echo -e "${GREEN}[INFO] Stopping ngrok (PID: $NGROK_PID)...${NC}"
    kill $NGROK_PID 2>/dev/null || echo -e "${YELLOW}[WARNING] ngrok process not found${NC}"
    rm /tmp/stuffed-lamb-ngrok.pid
else
    echo -e "${YELLOW}[INFO] ngrok PID file not found, trying by process name...${NC}"
    pkill ngrok || echo -e "${YELLOW}[WARNING] No ngrok process found${NC}"
fi

# Optionally stop Redis (commented out - you might want to keep Redis running)
# echo -e "${GREEN}[INFO] Stopping Redis...${NC}"
# redis-cli shutdown 2>/dev/null || echo -e "${YELLOW}[WARNING] Redis not running${NC}"

echo ""
echo -e "${GREEN}[SUCCESS] All services stopped${NC}"
echo ""

# Clean up log files (optional)
read -p "Delete log files? (y/N): " DELETE_LOGS
if [ "$DELETE_LOGS" = "y" ] || [ "$DELETE_LOGS" = "Y" ]; then
    rm -f /tmp/stuffed-lamb.log /tmp/stuffed-lamb-ngrok.log
    echo -e "${GREEN}[INFO] Log files deleted${NC}"
fi

echo ""

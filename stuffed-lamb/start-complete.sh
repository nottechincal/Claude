#!/bin/bash
# ======================================
# Stuffed Lamb Complete Startup - Linux/Mac
# Starts: Redis (optional) + Application + ngrok
# ======================================

set -e  # Exit on error

echo ""
echo "============================================"
echo "Stuffed Lamb VAPI Ordering System"
echo "Complete Startup (with ngrok tunnel)"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}[ERROR] .env file not found!${NC}"
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
    echo -e "${RED}[ERROR] Python 3 not found!${NC}"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check for ngrok
if command -v ngrok &> /dev/null; then
    NGROK_AVAILABLE=1
    echo -e "${GREEN}[INFO] ngrok found${NC}"
else
    NGROK_AVAILABLE=0
    echo -e "${YELLOW}[WARNING] ngrok not found!${NC}"
    echo ""
    echo "For VAPI integration, you need ngrok to expose your local server."
    echo ""
    echo "Download from: https://ngrok.com/download"
    echo ""
    echo "Alternatives:"
    echo "  1. Deploy to production (see PRODUCTION_DEPLOYMENT.md)"
    echo "  2. Use cloudflared tunnel"
    echo "  3. Deploy to cloud and skip ngrok"
    echo ""
    read -p "Continue without ngrok? (y/N): " CONTINUE
    if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
        echo ""
        echo "Exiting. Please install ngrok or deploy to production."
        exit 1
    fi
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}[INFO] Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}[WARNING] Virtual environment not found${NC}"
    echo -e "${GREEN}[INFO] Using system Python...${NC}"
fi

# Install/update dependencies
echo -e "${GREEN}[INFO] Checking dependencies...${NC}"
pip install -r requirements.txt --quiet || {
    echo -e "${RED}[ERROR] Failed to install dependencies${NC}"
    exit 1
}

# Check for Redis (optional)
echo ""
echo -e "${GREEN}[INFO] Checking for Redis...${NC}"
if command -v redis-server &> /dev/null; then
    if pgrep redis-server > /dev/null; then
        echo -e "${GREEN}[INFO] Redis is already running${NC}"
    else
        echo -e "${GREEN}[INFO] Starting Redis...${NC}"
        redis-server --daemonize yes
        sleep 2
    fi
else
    echo -e "${YELLOW}[WARNING] Redis not found - using in-memory sessions${NC}"
    echo -e "${YELLOW}[INFO] For production, install Redis:${NC}"
    echo "  - Linux: sudo apt-get install redis-server"
    echo "  - Mac: brew install redis"
    echo "  - Or Docker: docker run -d -p 6379:6379 redis:alpine"
fi

# Start the application server in background
echo ""
echo -e "${GREEN}[INFO] Starting Stuffed Lamb application server...${NC}"
python3 run.py > /tmp/stuffed-lamb.log 2>&1 &
SERVER_PID=$!
echo $SERVER_PID > /tmp/stuffed-lamb.pid

# Wait for server to start
echo -e "${GREEN}[INFO] Waiting for server to start...${NC}"
sleep 5

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}[SUCCESS] Server is running on http://localhost:8000${NC}"
else
    echo -e "${YELLOW}[WARNING] Server health check failed${NC}"
    echo -e "${YELLOW}[INFO] Server might still be starting...${NC}"
    echo -e "${YELLOW}[INFO] Check logs: tail -f /tmp/stuffed-lamb.log${NC}"
fi

# Start ngrok if available
if [ $NGROK_AVAILABLE -eq 1 ]; then
    echo ""
    echo -e "${GREEN}[INFO] Starting ngrok tunnel...${NC}"
    ngrok http 8000 > /tmp/stuffed-lamb-ngrok.log 2>&1 &
    NGROK_PID=$!
    echo $NGROK_PID > /tmp/stuffed-lamb-ngrok.pid
    sleep 3

    # Get ngrok URL
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok[^"]*' | head -1)

    echo ""
    echo "============================================"
    echo -e "${GREEN}SUCCESS! All services started${NC}"
    echo "============================================"
    echo ""
    echo -e "${BLUE}Application:${NC}  http://localhost:8000"
    echo -e "${BLUE}Health Check:${NC} http://localhost:8000/health"
    echo ""
    echo -e "${GREEN}NGROK TUNNEL:${NC}"
    if [ -n "$NGROK_URL" ]; then
        echo -e "${BLUE}Public URL:${NC}   $NGROK_URL"
        echo -e "${BLUE}VAPI Webhook:${NC} $NGROK_URL/vapi/webhook"
    else
        echo -e "${YELLOW}  - Check ngrok dashboard: http://localhost:4040${NC}"
        echo -e "${YELLOW}  - Your URL: https://xxxx.ngrok-free.app${NC}"
    fi
    echo ""
    echo -e "${BLUE}Ngrok Dashboard:${NC} http://localhost:4040"
    echo ""
else
    echo ""
    echo "============================================"
    echo -e "${GREEN}Server started (without ngrok)${NC}"
    echo "============================================"
    echo ""
    echo -e "${BLUE}Application:${NC}  http://localhost:8000"
    echo -e "${BLUE}Health Check:${NC} http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}[WARNING] VAPI integration will NOT work without public URL${NC}"
    echo -e "${YELLOW}[INFO] Install ngrok or deploy to production${NC}"
    echo ""
fi

echo -e "${GREEN}Process IDs saved:${NC}"
echo "  Server: /tmp/stuffed-lamb.pid (PID: $SERVER_PID)"
if [ $NGROK_AVAILABLE -eq 1 ]; then
    echo "  ngrok:  /tmp/stuffed-lamb-ngrok.pid (PID: $NGROK_PID)"
fi
echo ""
echo -e "${BLUE}To view logs:${NC}"
echo "  tail -f /tmp/stuffed-lamb.log"
echo ""
echo -e "${BLUE}To stop services:${NC}"
echo "  kill $SERVER_PID"
if [ $NGROK_AVAILABLE -eq 1 ]; then
    echo "  kill $NGROK_PID"
fi
echo ""
echo -e "${GREEN}Services are running in background. Press Ctrl+C to exit this script.${NC}"
echo -e "${YELLOW}(Note: Services will continue running after you exit)${NC}"
echo ""

# Keep script running to show it's active
trap "echo ''; echo 'Script terminated. Services still running in background.'; exit 0" INT TERM

tail -f /tmp/stuffed-lamb.log

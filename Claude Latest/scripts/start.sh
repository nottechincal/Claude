#!/usr/bin/env bash
# ============================================================
# Kebabalab VAPI Server – Start Script
# ============================================================
# Starts the Flask server, opens an ngrok tunnel, then updates
# VAPI with the live webhook URL automatically.
#
# Usage:
#   ./scripts/start.sh               # auto-detects ngrok
#   ./scripts/start.sh --no-ngrok    # skip ngrok (if you have a prod URL)
#
# Requirements:
#   pip install -r requirements.txt
#   ngrok installed (https://ngrok.com/download)
# ============================================================

set -e
cd "$(dirname "$0")/.."

# ── Load environment ─────────────────────────────────────────
if [ -f .env ]; then
  set -a
  source .env
  set +a
  echo "[env] Loaded .env"
fi

PORT="${PORT:-8000}"
VAPI_API_KEY="${VAPI_API_KEY}"
VAPI_ASSISTANT_ID="${VAPI_ASSISTANT_ID}"

if [ -z "$VAPI_API_KEY" ]; then
  echo "[error] VAPI_API_KEY not set. Check your .env file."
  exit 1
fi

# ── Start Flask server ───────────────────────────────────────
echo ""
echo "Starting Kebabalab server on port $PORT …"
python3 kebabalab/server.py &
SERVER_PID=$!
echo "[server] PID $SERVER_PID"

# Wait for server to be ready
for i in $(seq 1 10); do
  if curl -s http://localhost:$PORT/health >/dev/null 2>&1; then
    echo "[server] ✓ Healthy"
    break
  fi
  sleep 1
done

# ── Start ngrok ──────────────────────────────────────────────
if [ "$1" != "--no-ngrok" ]; then
  if ! command -v ngrok &>/dev/null; then
    echo "[ngrok] ngrok not found. Install from https://ngrok.com/download"
    echo "[ngrok] Skipping tunnel – server is running on localhost only."
    WEBHOOK_BASE="http://localhost:$PORT"
  else
    echo ""
    echo "Starting ngrok tunnel …"
    ngrok http $PORT --log=stdout > /tmp/ngrok_kebabalab.log 2>&1 &
    NGROK_PID=$!
    sleep 5

    # Extract ngrok URL
    WEBHOOK_BASE=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
      | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['tunnels'][0]['public_url'])" 2>/dev/null)

    if [ -z "$WEBHOOK_BASE" ]; then
      echo "[ngrok] ✗ Could not get tunnel URL from ngrok API"
      echo "[ngrok] Check /tmp/ngrok_kebabalab.log for details"
      WEBHOOK_BASE="http://localhost:$PORT"
    else
      echo "[ngrok] ✓ Tunnel active: $WEBHOOK_BASE"
    fi
  fi
else
  WEBHOOK_BASE="${SERVER_URL:-http://localhost:$PORT}"
  echo "[webhook] Using $WEBHOOK_BASE"
fi

# ── Update VAPI webhook URLs ─────────────────────────────────
if [[ "$WEBHOOK_BASE" != "http://localhost"* ]]; then
  echo ""
  echo "Updating VAPI webhook URLs → $WEBHOOK_BASE …"
  python3 scripts/vapi_setup.py --update-webhook "$WEBHOOK_BASE"
else
  echo ""
  echo "[vapi] ⚠  Webhook is localhost – VAPI tools will not work until you deploy."
  echo "[vapi]    Run: python3 scripts/vapi_setup.py --update-webhook https://your-url.ngrok-free.app"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Kebabalab is running!                                   ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  Local:    http://localhost:$PORT                         ║"
echo "║  Webhook:  $WEBHOOK_BASE/webhook"
echo "║  Health:   $WEBHOOK_BASE/health"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# ── Keep running ─────────────────────────────────────────────
wait $SERVER_PID

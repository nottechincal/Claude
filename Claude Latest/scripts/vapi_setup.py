#!/usr/bin/env python3
"""
Kebabalab VAPI Full Setup Script
=================================
Performs complete VAPI configuration:
  1. Validates API key + fetches current assistant state
  2. Deletes all old tools currently attached to the assistant
  3. Creates all 18 new tools with the given webhook URL
  4. Updates assistant: new tools, new system prompt, gpt-4o model, proper voice config

Usage:
    python scripts/vapi_setup.py [WEBHOOK_URL]

    WEBHOOK_URL   Your public-facing webhook base URL, e.g.
                  https://abc123.ngrok-free.app
                  Defaults to http://localhost:8000 (for local testing only)

Examples:
    python scripts/vapi_setup.py https://abc123.ngrok-free.app
    python scripts/vapi_setup.py  # uses localhost placeholder
"""

import json
import os
import sys
import time

import requests as _req

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))
except ImportError:
    pass

VAPI_BASE = "https://api.vapi.ai"
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "4000447a-37e5-4aa6-b7b3-e692bec2706f")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "977a1a1a-de18-4e2c-9e81-216b6b17dde9")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
TOOLS_FILE = os.path.join(BASE_DIR, "config", "vapi-tools-simplified.json")
PROMPT_FILE = os.path.join(BASE_DIR, "config", "system-prompt-simplified.md")
OUTPUT_FILE = os.path.join(BASE_DIR, "config", "vapi-tool-ids.json")


# ──────────────────────────────────────────────────────────────────────────────
# HTTP helpers (uses requests library for proper TLS/cert handling)
# ──────────────────────────────────────────────────────────────────────────────

def _headers():
    return {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }


def _get(path):
    r = _req.get(f"{VAPI_BASE}{path}", headers=_headers(), timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def _post(path, body):
    r = _req.post(f"{VAPI_BASE}{path}", headers=_headers(), json=body, timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def _patch(path, body):
    r = _req.patch(f"{VAPI_BASE}{path}", headers=_headers(), json=body, timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text


def _delete(path):
    r = _req.delete(f"{VAPI_BASE}{path}", headers=_headers(), timeout=15)
    try:
        return r.status_code, r.json() if r.text else {}
    except Exception:
        return r.status_code, r.text


# ──────────────────────────────────────────────────────────────────────────────
# Pretty printing
# ──────────────────────────────────────────────────────────────────────────────

def ok(msg):  print(f"  ✓  {msg}")
def fail(msg): print(f"  ✗  {msg}")
def info(msg): print(f"     {msg}")
def sep():     print("─" * 62)
def header(t): sep(); print(f"  {t}"); sep()


# ──────────────────────────────────────────────────────────────────────────────
# Step 1 – validate API key / fetch assistant
# ──────────────────────────────────────────────────────────────────────────────

def get_assistant():
    status, data = _get(f"/assistant/{VAPI_ASSISTANT_ID}")
    if status != 200:
        raise SystemExit(f"[ERROR] Could not fetch assistant {VAPI_ASSISTANT_ID}: HTTP {status}\n{data}")
    return data


# ──────────────────────────────────────────────────────────────────────────────
# Step 2 – delete old tools
# ──────────────────────────────────────────────────────────────────────────────

def delete_old_tools(assistant: dict) -> list:
    old_ids = (assistant.get("model") or {}).get("toolIds") or []
    if not old_ids:
        info("No existing tools found on assistant.")
        return []

    print(f"  Found {len(old_ids)} existing tool(s) to remove:")
    removed = []
    for tid in old_ids:
        status, resp = _delete(f"/tool/{tid}")
        if status in (200, 201, 204):
            ok(f"Deleted tool {tid}")
            removed.append(tid)
        else:
            fail(f"Delete {tid}: HTTP {status} – {str(resp)[:80]}")
        time.sleep(0.3)
    return removed


# ──────────────────────────────────────────────────────────────────────────────
# Step 3 – create 18 new tools
# ──────────────────────────────────────────────────────────────────────────────

def create_tools(webhook_base: str) -> list:
    webhook_url = webhook_base.rstrip("/") + "/webhook"
    print(f"  Webhook URL: {webhook_url}")

    with open(TOOLS_FILE) as f:
        config = json.load(f)

    tools_def = config["tools"]
    print(f"  Creating {len(tools_def)} tools …\n")

    created = []
    failed = []

    for i, tool in enumerate(tools_def, 1):
        name = tool["function"]["name"]
        # Inject the real webhook URL
        tool["server"]["url"] = webhook_url

        status, resp = _post("/tool", tool)
        if status in (200, 201):
            tid = resp.get("id", "?")
            ok(f"[{i:2d}/18] {name:<28} → {tid}")
            created.append({"name": name, "id": tid})
        else:
            fail(f"[{i:2d}/18] {name:<28} – HTTP {status}: {str(resp)[:80]}")
            failed.append(name)
        time.sleep(0.4)

    return created, failed


# ──────────────────────────────────────────────────────────────────────────────
# Step 4 – update assistant
# ──────────────────────────────────────────────────────────────────────────────

def update_assistant(created_tools: list, webhook_base: str, assistant: dict):
    tool_ids = [t["id"] for t in created_tools]
    webhook_url = webhook_base.rstrip("/") + "/webhook"

    with open(PROMPT_FILE) as f:
        system_prompt = f.read()

    # Preserve existing voice settings (ElevenLabs)
    existing_voice = assistant.get("voice", {
        "provider": "11labs",
        "voiceId": "Y0bYnHupCSm7PZ8v5V7B",
        "model": "eleven_flash_v2_5",
        "stability": 0.5,
        "similarityBoost": 0.75,
    })

    payload = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",  # upgrade from gpt-4o-mini
            "toolIds": tool_ids,
            "messages": [{"role": "system", "content": system_prompt}],
        },
        "voice": existing_voice,
        "server": {
            "url": webhook_url,
            "timeoutSeconds": 20,
        },
        "firstMessage": "Hi, Kebabalab St Kilda. What can I get for you?",
        "voicemailMessage": "Sorry we missed you. Please call back between 11am and 2am.",
        "endCallMessage": "Goodbye!",
        "endCallFunctionEnabled": True,
        "backgroundDenoisingEnabled": True,
        "backgroundSound": "off",
    }

    status, resp = _patch(f"/assistant/{VAPI_ASSISTANT_ID}", payload)
    if status in (200, 201):
        ok(f"Assistant updated: {VAPI_ASSISTANT_ID}")
        ok(f"Model:   gpt-4o")
        ok(f"Tools:   {len(tool_ids)}")
        ok(f"Webhook: {webhook_url}")
    else:
        fail(f"Assistant update failed: HTTP {status}")
        info(str(resp)[:300])
    return status in (200, 201)


# ──────────────────────────────────────────────────────────────────────────────
# Step 5 – update webhook URLs only (for when server moves)
# ──────────────────────────────────────────────────────────────────────────────

def update_webhook_only(new_webhook_base: str):
    """
    Update only the webhook URL on all tools + assistant.
    Used by start.sh after getting a new ngrok URL without re-creating tools.
    """
    webhook_url = new_webhook_base.rstrip("/") + "/webhook"

    # Load saved tool IDs
    if not os.path.exists(OUTPUT_FILE):
        raise SystemExit(f"[ERROR] {OUTPUT_FILE} not found. Run full setup first.")

    with open(OUTPUT_FILE) as f:
        saved_tools = json.load(f)

    print(f"\n  Updating {len(saved_tools)} tool webhook URLs → {webhook_url}\n")
    for tool in saved_tools:
        status, resp = _patch(f"/tool/{tool['id']}", {"server": {"url": webhook_url}})
        if status in (200, 201):
            ok(f"{tool['name']:<28} ✓")
        else:
            fail(f"{tool['name']:<28} HTTP {status}: {str(resp)[:60]}")
        time.sleep(0.2)

    # Update assistant server URL
    status, resp = _patch(f"/assistant/{VAPI_ASSISTANT_ID}", {
        "server": {"url": webhook_url, "timeoutSeconds": 20}
    })
    if status in (200, 201):
        ok(f"Assistant server URL updated")
    else:
        fail(f"Assistant update HTTP {status}: {str(resp)[:80]}")

    print(f"\n  ✓ Webhook URL updated to: {webhook_url}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    webhook_base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    # Special mode: just update webhooks
    if webhook_base == "--update-webhook":
        if len(sys.argv) < 3:
            raise SystemExit("Usage: vapi_setup.py --update-webhook https://your-url.ngrok-free.app")
        update_webhook_only(sys.argv[2])
        return

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        Kebabalab VAPI Full Setup                         ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\n  API Key:      {VAPI_API_KEY[:8]}…")
    print(f"  Assistant ID: {VAPI_ASSISTANT_ID}")
    print(f"  Webhook base: {webhook_base}")

    # ── Step 1 ───────────────────────────────────────────────────────────────
    header("Step 1: Fetching current assistant state")
    assistant = get_assistant()
    existing_tools = (assistant.get("model") or {}).get("toolIds") or []
    ok(f"Assistant '{assistant.get('name')}' – {len(existing_tools)} existing tool(s)")

    # ── Step 2 ───────────────────────────────────────────────────────────────
    header("Step 2: Deleting old tools")
    delete_old_tools(assistant)

    # ── Step 3 ───────────────────────────────────────────────────────────────
    header("Step 3: Creating 18 new tools")
    created, failed = create_tools(webhook_base)

    sep()
    print(f"\n  Created: {len(created)}/18   Failed: {len(failed)}")
    if failed:
        fail(f"Failed tools: {', '.join(failed)}")

    if not created:
        raise SystemExit("[ERROR] No tools created – aborting assistant update.")

    # Save tool IDs
    with open(OUTPUT_FILE, "w") as f:
        json.dump(created, f, indent=2)
    ok(f"Tool IDs saved → {OUTPUT_FILE}")

    # ── Step 4 ───────────────────────────────────────────────────────────────
    header("Step 4: Updating assistant")
    success = update_assistant(created, webhook_base, assistant)

    # ── Done ─────────────────────────────────────────────────────────────────
    sep()
    if success and len(failed) == 0:
        print("\n  🎉 Setup complete! Your assistant is ready.")
    elif success:
        print(f"\n  ⚠  Setup mostly complete – {len(failed)} tool(s) failed to create.")
    else:
        print("\n  ✗  Setup encountered errors – check output above.")

    if webhook_base.startswith("http://localhost"):
        print()
        print("  ⚠  WARNING: Webhook is set to localhost.")
        print("     VAPI cannot reach localhost from the cloud.")
        print("     Run this when you have a real server URL:")
        print("     python scripts/vapi_setup.py --update-webhook https://YOUR_URL")

    print()


if __name__ == "__main__":
    main()

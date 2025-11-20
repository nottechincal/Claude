"""Run realistic voice-like transcript checks against the Stuffed Lamb webhook tools.

This utility reuses the curated transcripts in data/voice_samples.json and
invokes quickAddItem through the Flask test client so you can verify
speech-to-item mapping without deploying anything.

Usage:
    python scripts/run_voice_samples.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

from stuffed_lamb.server import app, session_clear
import stuffed_lamb.server as server_module

VOICE_SAMPLES = Path(__file__).resolve().parent.parent / "data" / "voice_samples.json"
CALL_ID = "voice-smoke"
WEBHOOK_HEADERS = {
    "Content-Type": "application/json",
    "X-Stuffed-Lamb-Signature": server_module.WEBHOOK_SHARED_SECRET or "test-secret",
}


def _payload(description: str, phone: str) -> Dict[str, Any]:
    return {
        "message": {
            "type": "tool",
            "call": {"id": CALL_ID, "customer": {"number": phone}},
            "toolCalls": [
                {
                    "id": "quick-add-call",
                    "function": {
                        "name": "quickAddItem",
                        "arguments": {"description": description},
                    },
                }
            ],
        }
    }


def run_voice_regression() -> int:
    client = app.test_client()

    if not VOICE_SAMPLES.exists():
        print("voice_samples.json not found; aborting")
        return 1

    samples = json.loads(VOICE_SAMPLES.read_text())
    failures = 0

    for idx, sample in enumerate(samples):
        phone = f"+614000{idx:04d}"
        description = sample["description"]
        expected = sample["expected"]
        session_clear(phone)

        response = client.post("/webhook", json=_payload(description, phone), headers=WEBHOOK_HEADERS)
        body = response.get_json() or {}
        result = (body.get("results") or [{}])[0].get("result", {})

        item = result.get("item", {})
        ok = result.get("ok") and item.get("id") == expected.get("item_id")
        addons_ok = set(item.get("addons", [])) == set(expected.get("addons", []))
        extras_ok = set(item.get("extras", [])) == set(expected.get("extras", []))

        if ok and addons_ok and extras_ok:
            status = "PASS"
        else:
            status = "FAIL"
            failures += 1

        print(
            f"[{status}] #{idx+1}: '{description}' -> {item.get('id', 'unknown')} "
            f"addons={item.get('addons', [])} extras={item.get('extras', [])}"
        )

        session_clear(phone)

    print(f"\nCompleted {len(samples)} samples with {failures} failure(s)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_voice_regression())

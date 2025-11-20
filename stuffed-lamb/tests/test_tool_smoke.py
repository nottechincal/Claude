import os
import json
from typing import Dict, Any

import pytest

os.environ.setdefault("WEBHOOK_SHARED_SECRET", "test-secret")

from stuffed_lamb.server import app, session_clear, DatabaseConnection  # noqa: E402
import stuffed_lamb.server as server_module  # noqa: E402


def _build_payload(function_name: str, arguments: Dict[str, Any], call_id: str, phone: str) -> Dict[str, Any]:
    return {
        "message": {
            "type": "tool",
            "call": {"id": call_id, "customer": {"number": phone}},
            "toolCalls": [
                {
                    "id": f"{function_name}-call",
                    "function": {"name": function_name, "arguments": arguments},
                }
            ],
        }
    }


@pytest.fixture(autouse=True)
def stub_notifications(monkeypatch):
    monkeypatch.setattr(server_module, "_send_sms", lambda *_, **__: (True, None))
    monkeypatch.setattr(server_module, "_send_secondary_notification", lambda *_, **__: None)
    monkeypatch.setattr(server_module, "_enqueue_notification_job", lambda *_, **__: None)
    yield


@pytest.fixture
def webhook_headers():
    return {
        "Content-Type": "application/json",
        "X-Stuffed-Lamb-Signature": os.environ.get("WEBHOOK_SHARED_SECRET", "test-secret"),
    }


def _call_tool(client, function_name: str, arguments: Dict[str, Any], headers: Dict[str, str], call_id: str, phone: str):
    payload = _build_payload(function_name, arguments, call_id, phone)
    response = client.post("/webhook", json=payload, headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert body and "results" in body and body["results"], f"Empty response for {function_name}"
    return body["results"][0]["result"]


def test_webhook_tools_smoke(monkeypatch, webhook_headers):
    client = app.test_client()
    call_id = "smoke-call"
    phone = "0412345678"

    session_clear(phone)

    check = _call_tool(client, "checkOpen", {}, webhook_headers, call_id, phone)
    assert check["ok"] is True

    context = _call_tool(client, "getCallerSmartContext", {}, webhook_headers, call_id, phone)
    assert context["ok"] is True

    quick_add = _call_tool(
        client,
        "quickAddItem",
        {"description": "lamb mandi with nuts and sultanas"},
        webhook_headers,
        call_id,
        phone,
    )
    assert quick_add["ok"] is True

    multi = _call_tool(
        client,
        "addMultipleItemsToCart",
        {
            "items": [
                {
                    "id": "SOFT_DRINK",
                    "category": "drinks",
                    "name": "Soft Drink",
                    "brand": "Coke",
                    "quantity": 1,
                }
            ]
        },
        webhook_headers,
        call_id,
        phone,
    )
    assert multi["ok"] is True

    cart_state = _call_tool(client, "getCartState", {}, webhook_headers, call_id, phone)
    assert cart_state["ok"] is True
    assert cart_state["itemCount"] >= 2

    edited = _call_tool(
        client,
        "editCartItem",
        {"itemIndex": 0, "modifications": {"quantity": 2, "extras": ["tzatziki"]}},
        webhook_headers,
        call_id,
        phone,
    )
    assert edited["ok"] is True

    removed = _call_tool(client, "removeCartItem", {"itemIndex": 1}, webhook_headers, call_id, phone)
    assert removed["ok"] is True

    priced = _call_tool(client, "priceCart", {}, webhook_headers, call_id, phone)
    assert priced["ok"] is True

    summary = _call_tool(client, "getOrderSummary", {}, webhook_headers, call_id, phone)
    assert summary["ok"] is True

    pickup = _call_tool(client, "setPickupTime", {"requestedTime": "in 25 minutes"}, webhook_headers, call_id, phone)
    assert pickup["ok"] is True

    estimate = _call_tool(client, "estimateReadyTime", {}, webhook_headers, call_id, phone)
    assert estimate["ok"] is True

    order = _call_tool(
        client,
        "createOrder",
        {"customerName": "Smoke Test", "customerPhone": phone, "sendSMS": False},
        webhook_headers,
        call_id,
        phone,
    )
    assert order["ok"] is True

    receipt = _call_tool(client, "sendReceipt", {"phoneNumber": phone}, webhook_headers, call_id, phone)
    assert receipt["ok"] is True

    menu_link = _call_tool(client, "sendMenuLink", {"phoneNumber": phone}, webhook_headers, call_id, phone)
    assert menu_link["ok"] is True

    repeat = _call_tool(client, "repeatLastOrder", {"phoneNumber": phone}, webhook_headers, call_id, phone)
    assert repeat["ok"] is True
    assert repeat["itemCount"] >= 1

    end_call = _call_tool(client, "endCall", {}, webhook_headers, call_id, phone)
    assert end_call["ok"] is True

    with DatabaseConnection() as cursor:
        cursor.execute("DELETE FROM orders WHERE customer_phone = ?", (phone,))

    session_clear(phone)

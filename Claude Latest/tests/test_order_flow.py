import os

import pytest

from kebabalab.server import (
    DB_FILE,
    app,
    init_database,
    session_get,
    session_set,
    tool_convert_items_to_meals,
    tool_create_order,
    tool_edit_cart_item,
    tool_get_order_summary,
    tool_price_cart,
    tool_quick_add_item,
    tool_send_receipt,
    tool_set_pickup_time,
)


def _start_session(call_id: str):
    payload = {"message": {"call": {"id": call_id}}}
    ctx = app.test_request_context(json=payload)
    ctx.__enter__()
    session_set("cart", [])
    session_set("cart_priced", False)
    session_set("pickup_confirmed", False)
    return ctx


def _end_session(ctx):
    session_set("cart", [])
    ctx.__exit__(None, None, None)


def test_end_to_end_order_flow():
    ctx = _start_session("conversation-order")

    try:
        first_result = tool_quick_add_item(
            {
                "description": "Could I grab a small chicken kebab with lettuce, tomato, garlic and chilli sauce?",
            }
        )

        assert first_result["ok"] is True

        cart = session_get("cart", [])
        assert cart[0]["size"] == "small"
        assert set(cart[0]["salads"]) == {"lettuce", "tomato"}
        assert set(cart[0]["sauces"]) == {"garlic", "chilli"}

        price_snapshot = tool_price_cart({})
        assert price_snapshot["ok"] is True
        assert price_snapshot["total"] == pytest.approx(10.0)
        assert "GST" not in price_snapshot["message"].upper()

        meal_upgrade = tool_convert_items_to_meals(
            {"drinkBrand": "Coke", "chipsSize": "large", "chipsSalt": "chicken"}
        )

        assert meal_upgrade["ok"] is True
        cart = session_get("cart", [])
        assert cart[0]["is_combo"] is True
        assert cart[0]["chips_size"] == "large"
        assert cart[0]["drink_brand"].lower() == "coke"

        second_result = tool_quick_add_item(
            {
                "description": "Please add a chicken HSP with cheese plus garlic and chilli sauce.",
            }
        )

        assert second_result["ok"] is True

        cart = session_get("cart", [])
        assert "cheese" in cart[1]["extras"]
        assert cart[1]["cheese"] is True

        size_update = tool_edit_cart_item({"itemIndex": 1, "properties": {"size": "large"}})

        assert size_update["ok"] is True
        assert size_update["updatedItem"]["size"] == "large"
        assert size_update["updatedItem"]["price"] == pytest.approx(21.0)

        quantity_update = tool_edit_cart_item(
            {"itemIndex": 1, "properties": {"property": "quantity", "value": 2}}
        )

        assert quantity_update["ok"] is True
        assert session_get("cart", [])[1]["quantity"] == 2

        final_totals = tool_price_cart({})
        assert final_totals["ok"] is True
        assert final_totals["total"] == pytest.approx(62.0)
        assert final_totals["gst"] == 0
        assert "GST" not in final_totals["message"].upper()

        summary = tool_get_order_summary({})
        assert summary["ok"] is True
        assert "GST" not in summary["summary"].upper()

    finally:
        _end_session(ctx)


def test_set_pickup_time_enforces_minimum():
    ctx = _start_session("pickup-check")

    try:
        too_soon = tool_set_pickup_time({"requestedTime": "in 5 minutes"})
        assert too_soon["ok"] is False
        assert "10 minutes" in too_soon["error"]

        acceptable = tool_set_pickup_time({"requestedTime": "in 15 minutes"})
        assert acceptable["ok"] is True
        assert "15 minutes" in acceptable["message"]

    finally:
        _end_session(ctx)


def test_create_order_returns_short_display_number(tmp_path, monkeypatch):
    temp_db = tmp_path / "orders.db"
    monkeypatch.setenv("SHOP_ORDER_TO", "0423680596")

    original_db = DB_FILE
    try:
        # Point the module-level DB file to the temporary path
        from kebabalab import server as server_module

        server_module.DB_FILE = str(temp_db)
        init_database()

        sent_messages = []

        def fake_send_sms(phone, body):
            sent_messages.append((phone, body))
            return True, None

        monkeypatch.setattr(server_module, "_send_sms", fake_send_sms)

        ctx = _start_session("create-order")
        try:
            tool_quick_add_item({"description": "small chicken kebab with garlic sauce"})
            tool_price_cart({})
            tool_edit_cart_item({"itemIndex": 0, "properties": {"sauces": ["garlic", "chilli"]}})

            premature = tool_create_order({
                "customerName": "Tom",
                "customerPhone": "0423680596",
            })

            assert premature["ok"] is False
            assert "Pickup time" in premature["error"]

            tool_set_pickup_time({"requestedTime": "in 15 minutes"})

            result = tool_create_order({
                "customerName": "Tom",
                "customerPhone": "0423680596",
            })

            assert result["ok"] is True
            assert result["displayOrderNumber"].startswith("#")
            assert result["total"] == pytest.approx(10.0)
            assert "Order #" in result["message"]
            assert "GST" not in result["message"].upper()

            receipt = tool_send_receipt({"phoneNumber": "0423680596"})

            assert receipt["ok"] is True
            assert receipt["order"] == result["displayOrderNumber"]
            assert sent_messages, "Expected SMS messages to be recorded"
            assert "RECEIPT" in sent_messages[-1][1]
            assert "Garlic, Chilli" in sent_messages[-1][1]

        finally:
            _end_session(ctx)
    finally:
        from kebabalab import server as server_module

        server_module.DB_FILE = original_db
        if temp_db.exists():
            os.remove(temp_db)

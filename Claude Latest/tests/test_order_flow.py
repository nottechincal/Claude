import pytest

from server_simplified import (
    app,
    session_get,
    session_set,
    tool_convert_items_to_meals,
    tool_edit_cart_item,
    tool_price_cart,
    tool_quick_add_item,
)


def _start_session(call_id: str):
    payload = {"message": {"call": {"id": call_id}}}
    ctx = app.test_request_context(json=payload)
    ctx.__enter__()
    session_set("cart", [])
    session_set("cart_priced", False)
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
        assert price_snapshot["total"] == pytest.approx(11.0)

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
        assert final_totals["total"] > 0

    finally:
        _end_session(ctx)

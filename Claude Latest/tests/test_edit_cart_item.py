import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server_simplified import app, session_get, session_set, tool_edit_cart_item


def test_edit_cart_item_accepts_properties_payload():
    payload = {"message": {"call": {"id": "test-session"}}}

    with app.test_request_context(json=payload):
        session_set(
            "cart",
            [
                {
                    "category": "hsp",
                    "name": "Small Chicken HSP",
                    "size": "small",
                    "protein": "chicken",
                    "sauces": ["garlic", "chilli"],
                    "salads": [],
                    "extras": [],
                    "is_combo": False,
                    "quantity": 1,
                    "price": 15.0,
                }
            ],
        )

        result = tool_edit_cart_item({"itemIndex": 0, "properties": {"size": "large"}})

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
        assert result["updatedItem"]["price"] == 20.0
        assert result["updatedItem"]["name"].startswith("Large")

        cart = session_get("cart", [])
        assert cart[0]["size"] == "large"
        assert cart[0]["price"] == 20.0


def _setup_cart(app, item):
    payload = {"message": {"call": {"id": "test-session"}}}
    ctx = app.test_request_context(json=payload)
    ctx.__enter__()
    session_set("cart", [item])
    return ctx


def test_edit_cart_item_accepts_json_string_modifications():
    ctx = _setup_cart(
        app,
        {
            "category": "hsp",
            "name": "Small Chicken HSP",
            "size": "small",
            "protein": "chicken",
            "sauces": ["garlic", "chilli"],
            "salads": [],
            "extras": [],
            "is_combo": False,
            "quantity": 1,
            "price": 15.0,
        },
    )

    try:
        result = tool_edit_cart_item({"itemIndex": 0, "modifications": "{\"size\": \"large\"}"})

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
    finally:
        ctx.__exit__(None, None, None)


def test_edit_cart_item_accepts_properties_array():
    ctx = _setup_cart(
        app,
        {
            "category": "hsp",
            "name": "Small Chicken HSP",
            "size": "small",
            "protein": "chicken",
            "sauces": ["garlic", "chilli"],
            "salads": [],
            "extras": [],
            "is_combo": False,
            "quantity": 1,
            "price": 15.0,
        },
    )

    try:
        result = tool_edit_cart_item(
            {
                "itemIndex": 0,
                "properties": [{"property": "size", "value": "large"}],
            }
        )

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
    finally:
        ctx.__exit__(None, None, None)


def test_edit_cart_item_accepts_property_value_payload():
    ctx = _setup_cart(
        app,
        {
            "category": "hsp",
            "name": "Small Chicken HSP",
            "size": "small",
            "protein": "chicken",
            "sauces": ["garlic", "chilli"],
            "salads": [],
            "extras": [],
            "is_combo": False,
            "quantity": 1,
            "price": 15.0,
        },
    )

    try:
        result = tool_edit_cart_item(
            {
                "itemIndex": 0,
                "property": "size",
                "value": "large",
            }
        )

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
    finally:
        ctx.__exit__(None, None, None)


def test_edit_cart_item_accepts_embedded_property_dict():
    ctx = _setup_cart(
        app,
        {
            "category": "hsp",
            "name": "Small Chicken HSP",
            "size": "small",
            "protein": "chicken",
            "sauces": ["garlic", "chilli"],
            "salads": [],
            "extras": [],
            "is_combo": False,
            "quantity": 1,
            "price": 15.0,
        },
    )

    try:
        result = tool_edit_cart_item(
            {
                "itemIndex": 0,
                "properties": {"property": "size", "value": "large"},
            }
        )

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
    finally:
        ctx.__exit__(None, None, None)


def test_edit_cart_item_accepts_nested_value_maps():
    ctx = _setup_cart(
        app,
        {
            "category": "hsp",
            "name": "Small Chicken HSP",
            "size": "small",
            "protein": "chicken",
            "sauces": ["garlic", "chilli"],
            "salads": [],
            "extras": [],
            "is_combo": False,
            "quantity": 1,
            "price": 15.0,
        },
    )

    try:
        result = tool_edit_cart_item(
            {
                "itemIndex": 0,
                "properties": {"size": {"value": "large"}},
            }
        )

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
    finally:
        ctx.__exit__(None, None, None)


def test_edit_cart_item_accepts_pair_sequences():
    ctx = _setup_cart(
        app,
        {
            "category": "hsp",
            "name": "Small Chicken HSP",
            "size": "small",
            "protein": "chicken",
            "sauces": ["garlic", "chilli"],
            "salads": [],
            "extras": [],
            "is_combo": False,
            "quantity": 1,
            "price": 15.0,
        },
    )

    try:
        result = tool_edit_cart_item(
            {
                "itemIndex": 0,
                "properties": [["size", "large"], ["quantity", 2]],
            }
        )

        assert result["ok"] is True
        assert result["updatedItem"]["size"] == "large"
        assert result["updatedItem"]["quantity"] == 2
    finally:
        ctx.__exit__(None, None, None)

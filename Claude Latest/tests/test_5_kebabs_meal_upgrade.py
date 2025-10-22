"""
Test script for 5 kebabs with different modifications + meal upgrade

This simulates the scenario where:
1. Customer orders 5 kebabs with different modifications
2. Customer then asks to upgrade all to meals
3. Validates that the system handles this correctly
"""

import sys
import os

# Fix Windows encoding for emoji/unicode support
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from server_v2 import (
    tool_start_item_configuration,
    tool_set_item_property,
    tool_add_item_to_cart,
    tool_get_detailed_cart,
    tool_convert_items_to_meals,
    tool_price_cart,
    session_reset,
    session_get,
    session_set
)

def setup_session():
    """Reset session before each test"""
    session_reset()

def test_5_kebabs_different_modifications():
    """Test ordering 5 kebabs with different modifications"""
    setup_session()

    # Define 5 different kebabs
    kebabs = [
        {
            "size": "large",
            "protein": "lamb",
            "salads": ["lettuce", "tomato", "onion"],
            "sauces": ["garlic", "chilli"]
        },
        {
            "size": "large",
            "protein": "chicken",
            "salads": ["lettuce", "tomato"],
            "sauces": ["garlic"]
        },
        {
            "size": "large",
            "protein": "mixed",
            "salads": ["lettuce", "tomato", "onion", "tabouli"],
            "sauces": ["garlic", "bbq"]
        },
        {
            "size": "large",
            "protein": "lamb",
            "salads": ["lettuce", "onion"],
            "sauces": ["garlic", "chilli", "bbq"]
        },
        {
            "size": "large",
            "protein": "chicken",
            "salads": ["lettuce", "tomato", "tabouli"],
            "sauces": ["garlic"]
        }
    ]

    # Add each kebab to cart
    for idx, kebab_config in enumerate(kebabs):
        print(f"\n=== Adding Kebab #{idx + 1} ===")

        # Start configuration
        result = tool_start_item_configuration({"category": "kebabs"})
        assert result["ok"], f"Failed to start kebab #{idx + 1}: {result}"
        print(f"✓ Started configuration: {result}")

        # Set size
        result = tool_set_item_property({"field": "size", "value": kebab_config["size"]})
        assert result["ok"], f"Failed to set size for kebab #{idx + 1}: {result}"
        print(f"✓ Set size: {kebab_config['size']}")

        # Set protein
        result = tool_set_item_property({"field": "protein", "value": kebab_config["protein"]})
        assert result["ok"], f"Failed to set protein for kebab #{idx + 1}: {result}"
        print(f"✓ Set protein: {kebab_config['protein']}")

        # Set salads
        result = tool_set_item_property({"field": "salads", "value": kebab_config["salads"]})
        assert result["ok"], f"Failed to set salads for kebab #{idx + 1}: {result}"
        print(f"✓ Set salads: {kebab_config['salads']}")

        # Set sauces
        result = tool_set_item_property({"field": "sauces", "value": kebab_config["sauces"]})
        assert result["ok"], f"Failed to set sauces for kebab #{idx + 1}: {result}"
        print(f"✓ Set sauces: {kebab_config['sauces']}")

        # Add to cart
        result = tool_add_item_to_cart({})
        assert result["ok"], f"Failed to add kebab #{idx + 1} to cart: {result}"
        print(f"✓ Added to cart: {result}")

    # Check cart
    cart_result = tool_get_detailed_cart({})
    assert cart_result["ok"], f"Failed to get cart: {cart_result}"
    assert cart_result["itemCount"] == 5, f"Expected 5 items, got {cart_result['itemCount']}"

    print("\n=== Cart Before Meal Upgrade ===")
    for item in cart_result["items"]:
        print(f"[{item['index']}] {item['description']}")
        for mod in item['modifiers']:
            print(f"    {mod}")

    # Price cart before upgrade
    price_result = tool_price_cart({})
    assert price_result["ok"], f"Failed to price cart: {price_result}"
    print(f"\n✓ Total before upgrade: ${price_result['total']:.2f}")

    # Convert all to meals
    print("\n=== Converting All Kebabs to Meals ===")
    convert_result = tool_convert_items_to_meals({
        "drinkBrand": "coke",
        "chipsSize": "small",
        "chipsSalt": "chicken"
    })
    assert convert_result["ok"], f"Failed to convert to meals: {convert_result}"
    assert convert_result["convertedCount"] == 5, f"Expected 5 conversions, got {convert_result['convertedCount']}"
    print(f"✓ Converted {convert_result['convertedCount']} kebabs to meals")

    # Check cart after upgrade
    cart_result = tool_get_detailed_cart({})
    assert cart_result["ok"], f"Failed to get cart after upgrade: {cart_result}"
    assert cart_result["itemCount"] == 5, f"Expected 5 items after upgrade, got {cart_result['itemCount']}"

    print("\n=== Cart After Meal Upgrade ===")
    for item in cart_result["items"]:
        print(f"[{item['index']}] {item['description']}")
        for mod in item['modifiers']:
            print(f"    {mod}")
        assert item["isCombo"], f"Item {item['index']} should be a combo/meal"

    # Price cart after upgrade
    price_result = tool_price_cart({})
    assert price_result["ok"], f"Failed to price cart after upgrade: {price_result}"
    print(f"\n✓ Total after upgrade: ${price_result['total']:.2f}")

    # Verify pricing is correct
    # 5 large kebab meals = 5 × $22 = $110
    expected_total = 110.0
    assert abs(price_result["total"] - expected_total) < 0.01, \
        f"Expected total ${expected_total:.2f}, got ${price_result['total']:.2f}"

    print(f"\n✅ Test passed! All 5 kebabs converted to meals correctly")
    print(f"   Expected: ${expected_total:.2f}, Got: ${price_result['total']:.2f}")

def test_partial_meal_upgrade():
    """Test upgrading only specific kebabs to meals"""
    setup_session()

    print("\n=== Testing Partial Meal Upgrade ===")

    # Add 3 kebabs
    for i in range(3):
        tool_start_item_configuration({"category": "kebabs"})
        tool_set_item_property({"field": "size", "value": "large"})
        tool_set_item_property({"field": "protein", "value": "chicken"})
        tool_set_item_property({"field": "salads", "value": ["lettuce", "tomato"]})
        tool_set_item_property({"field": "sauces", "value": ["garlic"]})
        tool_add_item_to_cart({})

    # Convert only first and third kebabs (indices 0 and 2)
    convert_result = tool_convert_items_to_meals({
        "itemIndices": [0, 2],
        "drinkBrand": "sprite",
        "chipsSize": "small",
        "chipsSalt": "chicken"
    })

    assert convert_result["ok"], f"Failed to convert specific items: {convert_result}"
    assert convert_result["convertedCount"] == 2, f"Expected 2 conversions, got {convert_result['convertedCount']}"

    # Check cart
    cart_result = tool_get_detailed_cart({})
    assert cart_result["itemCount"] == 3, "Should still have 3 items"

    # Verify: item 0 and 2 should be meals, item 1 should be regular kebab
    assert cart_result["items"][0]["isCombo"], "Item 0 should be a meal"
    assert not cart_result["items"][1]["isCombo"], "Item 1 should NOT be a meal"
    assert cart_result["items"][2]["isCombo"], "Item 2 should be a meal"

    print("✅ Partial upgrade test passed!")

def test_empty_cart_meal_upgrade():
    """Test that meal upgrade fails gracefully on empty cart"""
    setup_session()

    result = tool_convert_items_to_meals({})
    assert not result["ok"], "Should fail on empty cart"
    assert "empty" in result["error"].lower(), "Should mention empty cart"

    print("✅ Empty cart test passed!")

def test_no_kebabs_in_cart():
    """Test meal upgrade when cart has no kebabs"""
    setup_session()

    # Add chips (not a kebab)
    tool_start_item_configuration({"category": "chips"})
    tool_set_item_property({"field": "size", "value": "large"})
    tool_add_item_to_cart({})

    result = tool_convert_items_to_meals({})
    assert not result["ok"], "Should fail when no kebabs in cart"
    assert "no kebabs" in result["error"].lower(), "Should mention no kebabs"

    print("✅ No kebabs test passed!")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing 5 Kebabs + Meal Upgrade Scenario")
    print("=" * 60)

    try:
        test_5_kebabs_different_modifications()
        print("\n" + "=" * 60)
        test_partial_meal_upgrade()
        print("\n" + "=" * 60)
        test_empty_cart_meal_upgrade()
        print("\n" + "=" * 60)
        test_no_kebabs_in_cart()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

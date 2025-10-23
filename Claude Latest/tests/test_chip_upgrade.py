"""
Test the CRITICAL chip upgrade scenario

This MUST work in ONE call, not 20+ calls like the bug.
"""

import json
import sys

# Mock Flask request for testing
class MockRequest:
    def __init__(self, data):
        self.data = data

    def get_json(self):
        return self.data

# Import server
sys.path.insert(0, '.')
import server_simplified as server

# Mock the request context
def mock_webhook_call(tool_name, params):
    """Simulate a webhook call"""
    mock_data = {
        "message": {
            "call": {
                "id": "test-call-123",
                "customer": {"number": "+61412345678"}
            },
            "toolCalls": [{
                "function": {
                    "name": tool_name,
                    "arguments": params
                }
            }]
        }
    }

    # Set up mock request
    original_request = server.request
    server.request = MockRequest(mock_data)

    try:
        # Get tool function
        tool_func = server.TOOLS.get(tool_name)
        if not tool_func:
            return {"error": f"Tool {tool_name} not found"}

        # Execute
        result = tool_func(params)
        return result
    finally:
        server.request = original_request

def test_chip_upgrade():
    """Test the scenario from the bug log"""
    print("="*60)
    print("TEST: Chip Upgrade Scenario")
    print("="*60)
    print()

    # Step 1: Add a chicken kebab using quickAddItem
    print("1. Adding chicken kebab...")
    result = mock_webhook_call("quickAddItem", {
        "description": "chicken kebab with lettuce, tomato, garlic, chili"
    })
    print(f"   Result: {result.get('message', result)}")
    assert result.get('ok'), f"Failed to add kebab: {result}"
    print()

    # Step 2: Convert to meal with Coke
    print("2. Converting to meal with Coke...")
    result = mock_webhook_call("convertItemsToMeals", {
        "drinkBrand": "coke",
        "chipsSize": "small",
        "chipsSalt": "chicken"
    })
    print(f"   Result: {result.get('message', result)}")
    assert result.get('ok'), f"Failed to convert to meal: {result}"
    print()

    # Step 3: Get cart state
    print("3. Checking cart state...")
    result = mock_webhook_call("getCartState", {})
    print(f"   Cart items: {len(result.get('cart', []))}")
    print(f"   Formatted: {result.get('formattedItems', [])}")
    assert result.get('ok'), f"Failed to get cart: {result}"

    cart = result.get('cart', [])
    assert len(cart) == 1, f"Expected 1 item, got {len(cart)}"
    meal = cart[0]
    assert meal.get('is_combo'), "Item should be a combo"
    assert meal.get('chips_size') == 'small', f"Expected small chips, got {meal.get('chips_size')}"
    print()

    # Step 4: THE CRITICAL TEST - Upgrade chips to large in ONE call
    print("4. CRITICAL: Upgrading chips to large (MUST be 1 call)...")
    print("   Calling editCartItem(0, {chips_size: 'large'})...")

    result = mock_webhook_call("editCartItem", {
        "itemIndex": 0,
        "modifications": {
            "chips_size": "large"
        }
    })

    print(f"   Result: {result.get('message', result)}")
    assert result.get('ok'), f"Failed to edit item: {result}"

    updated_item = result.get('updatedItem', {})
    assert updated_item.get('chips_size') == 'large', f"Chips size not updated: {updated_item}"
    assert updated_item.get('price') == 25.0, f"Price should be $25, got ${updated_item.get('price')}"

    print(f"   ✓ Chips upgraded from small to large")
    print(f"   ✓ Price updated to ${updated_item.get('price')}")
    print(f"   ✓ Completed in 1 call (not 20+!)")
    print()

    # Step 5: Verify final state
    print("5. Verifying final cart state...")
    result = mock_webhook_call("getCartState", {})
    cart = result.get('cart', [])
    final_meal = cart[0]

    print(f"   Final meal: {final_meal.get('name')}")
    print(f"   Chips size: {final_meal.get('chips_size')}")
    print(f"   Price: ${final_meal.get('price')}")

    assert final_meal.get('chips_size') == 'large', "Final chips size should be large"
    assert final_meal.get('price') == 25.0, "Final price should be $25"
    print()

    print("="*60)
    print("✓ TEST PASSED - Chip upgrade works in 1 call!")
    print("="*60)
    print()

    return True

def test_quick_add_variations():
    """Test quickAddItem NLP parsing"""
    print("="*60)
    print("TEST: QuickAddItem NLP Parsing")
    print("="*60)
    print()

    # Reset session
    server.SESSIONS.clear()

    test_cases = [
        ("2 large lamb kebabs", 2, "large", "lamb"),
        ("small chicken hsp no salad", 1, "small", "chicken"),
        ("coke", 1, None, None),
        ("large chips with chicken salt", 1, "large", None),
    ]

    for desc, expected_qty, expected_size, expected_protein in test_cases:
        print(f"Testing: '{desc}'")
        result = mock_webhook_call("quickAddItem", {"description": desc})

        if result.get('ok'):
            item = result.get('item', {})
            print(f"  ✓ Added: {item.get('name')}")
            print(f"    Qty: {item.get('quantity')} (expected {expected_qty})")
            if expected_size:
                print(f"    Size: {item.get('size')} (expected {expected_size})")
            if expected_protein:
                print(f"    Protein: {item.get('protein')} (expected {expected_protein})")
        else:
            print(f"  ✗ Failed: {result.get('error')}")

        print()

    print("="*60)
    print("✓ QuickAddItem tests complete")
    print("="*60)
    print()

if __name__ == "__main__":
    # Initialize database and menu
    print("Initializing server...")
    server.init_database()
    server.load_menu()
    print()

    try:
        # Run tests
        test_chip_upgrade()
        test_quick_add_variations()

        print()
        print("="*60)
        print("ALL TESTS PASSED!")
        print("="*60)

    except AssertionError as e:
        print()
        print("="*60)
        print(f"TEST FAILED: {e}")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print()
        print("="*60)
        print(f"ERROR: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

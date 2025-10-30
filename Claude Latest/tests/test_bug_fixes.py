#!/usr/bin/env python3
"""
Test the two critical bug fixes:
1. "no cheese" exclusion in parse_extras()
2. HSP combo size change pricing in editCartItem()
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kebabalab'))

from server import app, parse_extras, tool_quick_add_item, tool_edit_cart_item, tool_convert_items_to_meals, session_set, session_get
import json

def test_no_cheese_exclusion():
    """Test Bug #1: 'no cheese' should exclude cheese from extras"""
    print("\n" + "="*60)
    print("TEST 1: 'no cheese' exclusion")
    print("="*60)

    test_cases = [
        ("large chicken hsp with no cheese, just barbecue sauce", []),
        ("small lamb hsp without cheese", []),
        ("large mixed hsp hold the cheese", []),
        ("small chicken hsp with cheese", ["cheese"]),
        ("large lamb hsp", []),  # No explicit cheese mentioned
    ]

    for text, expected_extras in test_cases:
        result = parse_extras(text)
        status = "✅ PASS" if result == expected_extras else "❌ FAIL"
        print(f"{status} | Text: '{text}'")
        print(f"        Expected: {expected_extras}, Got: {result}")

    print()

def test_hsp_combo_size_pricing():
    """Test Bug #2: HSP combo size change should update price"""
    print("\n" + "="*60)
    print("TEST 2: HSP combo size change pricing")
    print("="*60)

    with app.test_request_context(
        data=json.dumps({"sessionId": "test-session"}),
        content_type='application/json'
    ):
        # Clear cart
        session_set('cart', [])

        # Add small chicken HSP
        print("\n1. Adding small chicken HSP...")
        result = tool_quick_add_item({
            "description": "small chicken hsp with barbecue sauce"
        })
        print(f"   Result: {result.get('message', result.get('error'))}")

        # Convert to combo
        print("\n2. Converting to HSP combo with Coke...")
        result = tool_convert_items_to_meals({
            "drinkBrand": "coke"
        })
        print(f"   Result: {result.get('message', result.get('error'))}")

        # Check initial price
        cart = session_get('cart', [])
        if cart:
            initial_price = cart[0].get('price')
            print(f"   Initial price: ${initial_price:.2f} (Expected: $17.00)")

            # Change size to large
            print("\n3. Changing HSP combo size from small to large...")
            result = tool_edit_cart_item({
                "itemIndex": 0,
                "modifications": {
                    "size": "large"
                }
            })
            print(f"   Result: {result.get('message', result.get('error'))}")

            # Check updated price
            cart = session_get('cart', [])
            if cart:
                updated_price = cart[0].get('price')
                expected_price = 22.0

                if updated_price == expected_price:
                    print(f"   ✅ PASS: Price correctly updated to ${updated_price:.2f}")
                else:
                    print(f"   ❌ FAIL: Price is ${updated_price:.2f}, expected ${expected_price:.2f}")

                print(f"\n   Cart item after edit:")
                print(f"   {json.dumps(cart[0], indent=2)}")
            else:
                print("   ❌ FAIL: Cart is empty after edit")
        else:
            print("   ❌ FAIL: Cart is empty after conversion")

    print()

def test_no_cheese_in_quickadd():
    """Test Bug #1 integrated with quickAddItem"""
    print("\n" + "="*60)
    print("TEST 3: 'no cheese' in quickAddItem (integrated test)")
    print("="*60)

    with app.test_request_context(
        data=json.dumps({"sessionId": "test-session-2"}),
        content_type='application/json'
    ):
        # Clear cart
        session_set('cart', [])

        # Add HSP with "no cheese"
        print("\n1. Adding: 'large chicken hsp with no cheese, just barbecue sauce'")
        result = tool_quick_add_item({
            "description": "large chicken hsp with no cheese, just barbecue sauce"
        })
        print(f"   Result: {result.get('message', result.get('error'))}")

        # Check cart
        cart = session_get('cart', [])
        if cart:
            item = cart[0]
            has_cheese = item.get('cheese', False)
            extras = item.get('extras', [])

            print(f"\n   Cart item:")
            print(f"   - Category: {item.get('category')}")
            print(f"   - Cheese field: {has_cheese}")
            print(f"   - Extras: {extras}")
            print(f"   - Sauces: {item.get('sauces', [])}")

            if not has_cheese and 'cheese' not in extras:
                print(f"\n   ✅ PASS: Cheese correctly excluded")
            else:
                print(f"\n   ❌ FAIL: Cheese should be excluded but found in item")
        else:
            print("   ❌ FAIL: Cart is empty")

    print()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TESTING CRITICAL BUG FIXES")
    print("="*60)

    # Run tests
    test_no_cheese_exclusion()
    test_no_cheese_in_quickadd()
    test_hsp_combo_size_pricing()

    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)

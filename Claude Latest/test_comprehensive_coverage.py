#!/usr/bin/env python3
"""
Comprehensive Test Suite for Kebabalab VAPI System
Tests ALL possible combinations and conversation flows
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import server
from kebabalab import server

# Test tracking
tests_run = 0
tests_passed = 0
tests_failed = 0
test_results = []

def test_result(name: str, passed: bool, details: str = "", expected: Any = None, actual: Any = None):
    """Record test result with detailed information"""
    global tests_run, tests_passed, tests_failed, test_results
    tests_run += 1

    result = {
        "name": name,
        "passed": passed,
        "details": details,
        "expected": expected,
        "actual": actual,
        "timestamp": datetime.now().isoformat()
    }

    if passed:
        tests_passed += 1
        print(f"✅ PASS: {name}")
        if details:
            print(f"   {details}")
    else:
        tests_failed += 1
        print(f"❌ FAIL: {name}")
        if details:
            print(f"   {details}")
        if expected is not None:
            print(f"   Expected: {expected}")
        if actual is not None:
            print(f"   Actual: {actual}")

    test_results.append(result)

def create_vapi_webhook_payload(tool_name: str, arguments: dict, call_id: str = "test-call-123", phone: str = "+61412345678"):
    """Create a VAPI-formatted webhook payload"""
    return {
        "message": {
            "type": "tool-calls",
            "call": {
                "id": call_id,
                "type": "webCall",
                "customer": {
                    "number": phone
                },
                "status": "in-progress"
            },
            "toolCalls": [{
                "id": f"call_{tool_name}_{datetime.now().timestamp()}",
                "type": "function",
                "function": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }]
        }
    }

def call_webhook(payload: dict) -> Tuple[dict, int]:
    """Call the webhook endpoint and return response"""
    # Simulate webhook call by directly processing the payload
    # This is equivalent to what the webhook does
    try:
        message = payload.get('message', {})
        tool_calls = message.get('toolCalls', []) or []

        if not tool_calls:
            return {"status": "acknowledged", "message": "No tool calls to process"}, 200

        results = []

        for tool_call in tool_calls:
            function_data = tool_call.get('function', {})
            function_name = function_data.get('name', '')
            arguments = function_data.get('arguments', {})
            tool_call_id = tool_call.get('id')

            # Get the tool function
            tool_func = server.TOOLS.get(function_name)

            if not tool_func:
                results.append({
                    "toolCallId": tool_call_id,
                    "result": {"ok": False, "error": f"Unknown tool: {function_name}"}
                })
                continue

            # Execute the tool
            try:
                result = tool_func(arguments)
            except Exception as tool_error:
                result = {"ok": False, "error": str(tool_error)}

            results.append({
                "toolCallId": tool_call_id,
                "result": result
            })

        return {"results": results}, 200

    except Exception as e:
        return {"error": str(e)}, 500

def clear_session():
    """Clear session data"""
    server.session_clear()

print("="*70)
print("COMPREHENSIVE TEST SUITE - KEBABALAB VAPI SYSTEM")
print("="*70)
print()

# Initialize system
print("Initializing system...")
server.init_database()
server.load_menu()
print(f"✓ Menu loaded: {len(server.MENU.get('categories', {}))} categories")
print(f"✓ Tools available: {len(server.TOOLS)}")
print()

# ============================================================
# TEST CATEGORY 1: ALL PROTEINS WITH ALL SIZES
# ============================================================
print("🥙 TEST CATEGORY 1: ALL PROTEINS WITH ALL SIZES (KEBABS)")
print("-" * 70)

call_id = "test-proteins-001"
proteins = ["lamb", "chicken", "mixed", "falafel"]
sizes = ["small", "large"]
expected_prices = {
    "kebabs": {"small": 10.0, "large": 15.0},
    "hsp": {"small": 15.0, "large": 20.0}
}

for protein in proteins:
    for size in sizes:
        clear_session()

        # Test kebab
        payload = create_vapi_webhook_payload(
            "quickAddItem",
            {"description": f"{size} {protein} kebab"},
            call_id=call_id
        )
        response, status = call_webhook(payload)
        results = response.get('results', [])

        if results:
            result = results[0].get('result', {})
            item = result.get('item', {})

            test_result(
                f"Add {size} {protein} kebab",
                result.get('ok') == True and item.get('protein') == protein and item.get('size') == size,
                f"Price: ${item.get('price', 0)}, Status: {status}",
                expected_prices["kebabs"][size],
                item.get('price', 0)
            )

print()

# ============================================================
# TEST CATEGORY 2: ALL PROTEINS WITH ALL SIZES (HSPs)
# ============================================================
print("🍟 TEST CATEGORY 2: ALL PROTEINS WITH ALL SIZES (HSPs)")
print("-" * 70)

for protein in proteins:
    for size in sizes:
        clear_session()

        # Test HSP
        payload = create_vapi_webhook_payload(
            "quickAddItem",
            {"description": f"{size} {protein} hsp"},
            call_id=call_id
        )
        response, status = call_webhook(payload)
        results = response.get('results', [])

        if results:
            result = results[0].get('result', {})
            item = result.get('item', {})

            test_result(
                f"Add {size} {protein} HSP",
                result.get('ok') == True and item.get('protein') == protein and item.get('size') == size,
                f"Price: ${item.get('price', 0)}, Category: {item.get('category')}",
                expected_prices["hsp"][size],
                item.get('price', 0)
            )

print()

# ============================================================
# TEST CATEGORY 3: ALL SALADS COMBINATIONS
# ============================================================
print("🥗 TEST CATEGORY 3: ALL SALADS COMBINATIONS")
print("-" * 70)

salads = ["lettuce", "tomato", "onion", "pickles", "olives"]
salad_combinations = [
    ["lettuce"],
    ["lettuce", "tomato"],
    ["lettuce", "tomato", "onion"],
    ["lettuce", "tomato", "onion", "pickles"],
    ["lettuce", "tomato", "onion", "pickles", "olives"],
    ["tomato", "pickles"],
    ["onion", "olives"]
]

for combo in salad_combinations:
    clear_session()

    salad_str = ", ".join(combo)
    payload = create_vapi_webhook_payload(
        "quickAddItem",
        {"description": f"large lamb kebab with {salad_str}"},
        call_id=call_id
    )
    response, status = call_webhook(payload)
    results = response.get('results', [])

    if results:
        result = results[0].get('result', {})
        item = result.get('item', {})
        item_salads = item.get('salads', [])

        test_result(
            f"Kebab with salads: {salad_str}",
            set(item_salads) == set(combo),
            f"Expected: {combo}, Got: {item_salads}",
            combo,
            item_salads
        )

print()

# ============================================================
# TEST CATEGORY 4: ALL SAUCES COMBINATIONS
# ============================================================
print("🥫 TEST CATEGORY 4: ALL SAUCES COMBINATIONS")
print("-" * 70)

sauces = ["garlic", "chilli", "bbq", "tomato", "sweet chilli", "mayo", "hummus"]
sauce_combinations = [
    ["garlic"],
    ["garlic", "chilli"],
    ["garlic", "chilli", "bbq"],
    ["bbq", "mayo"],
    ["hummus", "garlic"],
    ["sweet chilli", "mayo"]
]

for combo in sauce_combinations:
    clear_session()

    sauce_str = ", ".join(combo)
    payload = create_vapi_webhook_payload(
        "quickAddItem",
        {"description": f"large chicken kebab with {sauce_str}"},
        call_id=call_id
    )
    response, status = call_webhook(payload)
    results = response.get('results', [])

    if results:
        result = results[0].get('result', {})
        item = result.get('item', {})
        item_sauces = item.get('sauces', [])

        test_result(
            f"Kebab with sauces: {sauce_str}",
            set(item_sauces) == set(combo),
            f"Expected: {combo}, Got: {item_sauces}",
            combo,
            item_sauces
        )

print()

# ============================================================
# TEST CATEGORY 5: ALL EXCLUSIONS
# ============================================================
print("🚫 TEST CATEGORY 5: ALL EXCLUSIONS")
print("-" * 70)

exclusions = [
    ("no tomato", "tomato"),
    ("no onion", "onion"),
    ("no lettuce", "lettuce"),
    ("no pickles", "pickles"),
    ("no cheese", "cheese")
]

for exclusion_phrase, excluded_item in exclusions:
    clear_session()

    payload = create_vapi_webhook_payload(
        "quickAddItem",
        {"description": f"large lamb kebab {exclusion_phrase}"},
        call_id=call_id
    )
    response, status = call_webhook(payload)
    results = response.get('results', [])

    if results:
        result = results[0].get('result', {})
        item = result.get('item', {})
        item_salads = item.get('salads', [])
        item_extras = item.get('extras', [])

        # Check that excluded item is not present
        is_excluded = (
            excluded_item not in item_salads and
            excluded_item not in item_extras
        )

        test_result(
            f"Kebab with '{exclusion_phrase}'",
            is_excluded,
            f"Salads: {item_salads}, Extras: {item_extras}"
        )

print()

# ============================================================
# TEST CATEGORY 6: ALL EXTRAS
# ============================================================
print("➕ TEST CATEGORY 6: ALL EXTRAS")
print("-" * 70)

extras = ["cheese", "extra meat", "haloumi"]

for extra in extras:
    clear_session()

    payload = create_vapi_webhook_payload(
        "quickAddItem",
        {"description": f"large lamb kebab with {extra}"},
        call_id=call_id
    )
    response, status = call_webhook(payload)
    results = response.get('results', [])

    if results:
        result = results[0].get('result', {})
        item = result.get('item', {})
        item_extras = item.get('extras', [])

        test_result(
            f"Kebab with {extra}",
            extra in item_extras or (extra == "cheese" and item.get('cheese') == True),
            f"Extras: {item_extras}, Cheese: {item.get('cheese')}"
        )

print()

# ============================================================
# TEST CATEGORY 7: ALL CHIP VARIATIONS
# ============================================================
print("🍟 TEST CATEGORY 7: ALL CHIP VARIATIONS")
print("-" * 70)

chip_sizes = ["small", "large"]
salt_types = ["chicken salt", "normal salt", "no salt"]
expected_chip_prices = {"small": 5.0, "large": 9.0}

for size in chip_sizes:
    for salt in salt_types:
        clear_session()

        payload = create_vapi_webhook_payload(
            "quickAddItem",
            {"description": f"{size} chips with {salt}"},
            call_id=call_id
        )
        response, status = call_webhook(payload)
        results = response.get('results', [])

        if results:
            result = results[0].get('result', {})
            item = result.get('item', {})

            test_result(
                f"Add {size} chips with {salt}",
                result.get('ok') == True and item.get('size') == size,
                f"Price: ${item.get('price', 0)}",
                expected_chip_prices[size],
                item.get('price', 0)
            )

print()

# ============================================================
# TEST CATEGORY 8: ALL DRINKS
# ============================================================
print("🥤 TEST CATEGORY 8: ALL DRINKS")
print("-" * 70)

drinks = ["coke", "sprite", "fanta", "pepsi", "water"]
expected_drink_price = 3.5

for drink in drinks:
    clear_session()

    payload = create_vapi_webhook_payload(
        "quickAddItem",
        {"description": drink},
        call_id=call_id
    )
    response, status = call_webhook(payload)
    results = response.get('results', [])

    if results:
        result = results[0].get('result', {})
        item = result.get('item', {})

        test_result(
            f"Add {drink}",
            result.get('ok') == True and item.get('category') == 'drinks',
            f"Price: ${item.get('price', 0)}",
            expected_drink_price,
            item.get('price', 0)
        )

print()

# ============================================================
# TEST CATEGORY 9: MEAL CONVERSIONS - ALL COMBINATIONS
# ============================================================
print("🍱 TEST CATEGORY 9: MEAL CONVERSIONS - ALL COMBINATIONS")
print("-" * 70)

meal_drinks = ["coke", "sprite", "fanta"]
meal_chip_sizes = ["small", "large"]
meal_proteins = ["lamb", "chicken"]

for protein in meal_proteins:
    for drink in meal_drinks:
        for chip_size in meal_chip_sizes:
            clear_session()

            # Add kebab
            payload1 = create_vapi_webhook_payload(
                "quickAddItem",
                {"description": f"large {protein} kebab"},
                call_id=call_id
            )
            response1, _ = call_webhook(payload1)

            # Convert to meal
            payload2 = create_vapi_webhook_payload(
                "convertItemsToMeals",
                {"drinkBrand": drink, "chipsSize": chip_size},
                call_id=call_id
            )
            response2, _ = call_webhook(payload2)
            results2 = response2.get('results', [])

            if results2:
                result = results2[0].get('result', {})

                # Get cart to verify
                payload3 = create_vapi_webhook_payload(
                    "getCartState",
                    {},
                    call_id=call_id
                )
                response3, _ = call_webhook(payload3)
                results3 = response3.get('results', [])

                if results3:
                    cart_result = results3[0].get('result', {})
                    cart = cart_result.get('cart', [])

                    if cart:
                        meal = cart[0]
                        test_result(
                            f"Convert {protein} kebab to meal (drink: {drink}, chips: {chip_size})",
                            meal.get('is_combo') == True and
                            meal.get('drink_brand') == drink and
                            meal.get('chips_size') == chip_size,
                            f"Drink: {meal.get('drink_brand')}, Chips: {meal.get('chips_size')}"
                        )

print()

# ============================================================
# TEST CATEGORY 10: HSP COMBOS - ALL COMBINATIONS
# ============================================================
print("🌯 TEST CATEGORY 10: HSP COMBOS - ALL COMBINATIONS")
print("-" * 70)

hsp_proteins = ["lamb", "chicken", "mixed"]
hsp_drinks = ["coke", "sprite"]

for protein in hsp_proteins:
    for drink in hsp_drinks:
        clear_session()

        # Add HSP
        payload1 = create_vapi_webhook_payload(
            "quickAddItem",
            {"description": f"large {protein} hsp"},
            call_id=call_id
        )
        response1, _ = call_webhook(payload1)

        # Convert to combo
        payload2 = create_vapi_webhook_payload(
            "convertItemsToMeals",
            {"drinkBrand": drink},
            call_id=call_id
        )
        response2, _ = call_webhook(payload2)
        results2 = response2.get('results', [])

        if results2:
            result = results2[0].get('result', {})

            # Get cart to verify
            payload3 = create_vapi_webhook_payload(
                "getCartState",
                {},
                call_id=call_id
            )
            response3, _ = call_webhook(payload3)
            results3 = response3.get('results', [])

            if results3:
                cart_result = results3[0].get('result', {})
                cart = cart_result.get('cart', [])

                if cart:
                    combo = cart[0]
                    test_result(
                        f"Convert {protein} HSP to combo (drink: {drink})",
                        combo.get('is_combo') == True and combo.get('drink_brand') == drink,
                        f"Drink: {combo.get('drink_brand')}"
                    )

print()

# ============================================================
# TEST CATEGORY 11: CART MODIFICATIONS - EDIT ITEMS
# ============================================================
print("✏️ TEST CATEGORY 11: CART MODIFICATIONS - EDIT ITEMS")
print("-" * 70)

# Test editing salads
clear_session()
payload1 = create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab with lettuce, tomato"}, call_id=call_id)
call_webhook(payload1)

payload2 = create_vapi_webhook_payload("editCartItem", {"itemIndex": 0, "modifications": {"salads": ["lettuce", "onion"]}}, call_id=call_id)
response2, _ = call_webhook(payload2)
results2 = response2.get('results', [])

if results2:
    result = results2[0].get('result', {})
    updated_item = result.get('updatedItem', {})
    test_result(
        "Edit kebab salads",
        set(updated_item.get('salads', [])) == {"lettuce", "onion"},
        f"Salads: {updated_item.get('salads', [])}"
    )

# Test editing sauces
clear_session()
payload1 = create_vapi_webhook_payload("quickAddItem", {"description": "large chicken kebab"}, call_id=call_id)
call_webhook(payload1)

payload2 = create_vapi_webhook_payload("editCartItem", {"itemIndex": 0, "modifications": {"sauces": ["garlic", "chilli", "bbq"]}}, call_id=call_id)
response2, _ = call_webhook(payload2)
results2 = response2.get('results', [])

if results2:
    result = results2[0].get('result', {})
    updated_item = result.get('updatedItem', {})
    test_result(
        "Edit kebab sauces",
        set(updated_item.get('sauces', [])) == {"garlic", "chilli", "bbq"},
        f"Sauces: {updated_item.get('sauces', [])}"
    )

# Test editing chip size in meal
clear_session()
payload1 = create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id)
call_webhook(payload1)
payload2 = create_vapi_webhook_payload("convertItemsToMeals", {"drinkBrand": "coke", "chipsSize": "small"}, call_id=call_id)
call_webhook(payload2)

payload3 = create_vapi_webhook_payload("editCartItem", {"itemIndex": 0, "modifications": {"chips_size": "large"}}, call_id=call_id)
response3, _ = call_webhook(payload3)
results3 = response3.get('results', [])

if results3:
    result = results3[0].get('result', {})
    updated_item = result.get('updatedItem', {})
    test_result(
        "Upgrade meal chips from small to large",
        updated_item.get('chips_size') == "large",
        f"Chip size: {updated_item.get('chips_size')}"
    )

print()

# ============================================================
# TEST CATEGORY 12: CART MODIFICATIONS - REMOVE ITEMS
# ============================================================
print("🗑️ TEST CATEGORY 12: CART MODIFICATIONS - REMOVE ITEMS")
print("-" * 70)

clear_session()

# Add multiple items
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small chicken hsp"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "coke"}, call_id=call_id))

# Remove middle item
payload = create_vapi_webhook_payload("removeCartItem", {"itemIndex": 1}, call_id=call_id)
response, _ = call_webhook(payload)
results = response.get('results', [])

if results:
    result = results[0].get('result', {})

    # Verify cart has 2 items
    payload2 = create_vapi_webhook_payload("getCartState", {}, call_id=call_id)
    response2, _ = call_webhook(payload2)
    results2 = response2.get('results', [])

    if results2:
        cart_result = results2[0].get('result', {})
        cart = cart_result.get('cart', [])
        test_result(
            "Remove item from cart",
            len(cart) == 2,
            f"Cart has {len(cart)} items (expected 2)"
        )

print()

# ============================================================
# TEST CATEGORY 13: FULL CONVERSATION FLOWS
# ============================================================
print("💬 TEST CATEGORY 13: FULL CONVERSATION FLOWS")
print("-" * 70)

# Flow 1: Simple order with checkout
print("\nFlow 1: Simple order with checkout")
clear_session()
call_id = "flow-001"

steps = [
    ("quickAddItem", {"description": "large lamb kebab with lettuce, tomato, garlic"}),
    ("priceCart", {}),
    ("setPickupTime", {"requestedTime": "in 20 minutes"}),
    ("createOrder", {"customerName": "John Smith", "customerPhone": "+61412345678", "sendSMS": False})
]

flow_success = True
for tool_name, args in steps:
    payload = create_vapi_webhook_payload(tool_name, args, call_id=call_id)
    response, status = call_webhook(payload)
    results = response.get('results', [])

    if not results or not results[0].get('result', {}).get('ok'):
        flow_success = False
        break

test_result("Flow 1: Simple order checkout", flow_success, "All steps completed successfully")

# Flow 2: Multiple items with meal conversion
print("\nFlow 2: Multiple items with meal conversion")
clear_session()
call_id = "flow-002"

call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small chicken kebab"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small lamb kebab"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("convertItemsToMeals", {"drinkBrand": "coke", "chipsSize": "small"}, call_id=call_id))[0]
results = response.get('results', [])

if results:
    result = results[0].get('result', {})
    test_result(
        "Flow 2: Multiple items to meals",
        result.get('ok') == True and result.get('convertedCount') == 2,
        f"Converted {result.get('convertedCount')} items"
    )

# Flow 3: Order with modifications
print("\nFlow 3: Order with modifications")
clear_session()
call_id = "flow-003"

call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large chicken kebab with lettuce, tomato"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("editCartItem", {"itemIndex": 0, "modifications": {"salads": ["lettuce"], "sauces": ["garlic", "chilli"]}}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("priceCart", {}, call_id=call_id))[0]
results = response.get('results', [])

if results:
    result = results[0].get('result', {})
    test_result(
        "Flow 3: Order with modifications",
        result.get('ok') == True and result.get('total') == 15.0,
        f"Total: ${result.get('total')}"
    )

# Flow 4: Complex order (HSP combo with exclusions)
print("\nFlow 4: Complex HSP combo with exclusions")
clear_session()
call_id = "flow-004"

call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb hsp no onion"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("convertItemsToMeals", {"drinkBrand": "sprite"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("priceCart", {}, call_id=call_id))[0]
results = response.get('results', [])

if results:
    result = results[0].get('result', {})
    test_result(
        "Flow 4: HSP combo with exclusions",
        result.get('ok') == True and result.get('total') == 22.0,
        f"Total: ${result.get('total')} (expected $22 for large HSP combo)"
    )

# Flow 5: Multiple items, remove one, add more
print("\nFlow 5: Multiple items with removal")
clear_session()
call_id = "flow-005"

call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small chips"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "coke"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("removeCartItem", {"itemIndex": 1}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("getCartState", {}, call_id=call_id))[0]
results = response.get('results', [])

if results:
    cart_result = results[0].get('result', {})
    cart = cart_result.get('cart', [])
    test_result(
        "Flow 5: Add, remove, verify",
        len(cart) == 2 and cart[0].get('protein') == 'lamb',
        f"Cart has {len(cart)} items"
    )

print()

# ============================================================
# TEST CATEGORY 14: GST CALCULATIONS
# ============================================================
print("💰 TEST CATEGORY 14: GST CALCULATIONS")
print("-" * 70)

gst_test_cases = [
    (10.0, 0.91, "Small kebab"),
    (15.0, 1.36, "Large kebab"),
    (20.0, 1.82, "Two small kebabs"),
    (34.0, 3.09, "Two small kebab meals"),
    (43.0, 3.91, "Mixed order")
]

for total, expected_gst, description in gst_test_cases:
    clear_session()

    # Create order that totals the expected amount
    if total == 10.0:
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small lamb kebab"}, call_id=call_id))
    elif total == 15.0:
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id))
    elif total == 20.0:
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small lamb kebab"}, call_id=call_id))
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small chicken kebab"}, call_id=call_id))
    elif total == 34.0:
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small lamb kebab"}, call_id=call_id))
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small chicken kebab"}, call_id=call_id))
        call_webhook(create_vapi_webhook_payload("convertItemsToMeals", {"drinkBrand": "coke", "chipsSize": "small"}, call_id=call_id))
    elif total == 43.0:
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb hsp"}, call_id=call_id))
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large chips"}, call_id=call_id))
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "2 cokes"}, call_id=call_id))
        call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "small chips"}, call_id=call_id))

    response = call_webhook(create_vapi_webhook_payload("priceCart", {}, call_id=call_id))[0]
    results = response.get('results', [])

    if results:
        result = results[0].get('result', {})
        actual_gst = result.get('gst', 0)

        test_result(
            f"GST calculation: {description} (${total})",
            abs(actual_gst - expected_gst) < 0.01,
            f"GST: ${actual_gst:.2f}",
            expected_gst,
            actual_gst
        )

print()

# ============================================================
# TEST CATEGORY 15: ERROR HANDLING
# ============================================================
print("⚠️ TEST CATEGORY 15: ERROR HANDLING")
print("-" * 70)

# Test 1: Create order without items
clear_session()
response = call_webhook(create_vapi_webhook_payload("createOrder", {"customerName": "Test", "customerPhone": "+61412345678"}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    result = results[0].get('result', {})
    test_result(
        "Create order with empty cart",
        result.get('ok') == False and 'empty' in result.get('error', '').lower(),
        f"Error: {result.get('error')}"
    )

# Test 2: Edit non-existent item
clear_session()
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("editCartItem", {"itemIndex": 5, "modifications": {"salads": ["lettuce"]}}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    result = results[0].get('result', {})
    test_result(
        "Edit non-existent item",
        result.get('ok') == False,
        f"Error: {result.get('error')}"
    )

# Test 3: Remove non-existent item
clear_session()
response = call_webhook(create_vapi_webhook_payload("removeCartItem", {"itemIndex": 0}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    result = results[0].get('result', {})
    test_result(
        "Remove from empty cart",
        result.get('ok') == False,
        f"Error: {result.get('error')}"
    )

# Test 4: Create order without pickup time
clear_session()
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("createOrder", {"customerName": "Test", "customerPhone": "+61412345678"}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    result = results[0].get('result', {})
    test_result(
        "Create order without pickup time",
        result.get('ok') == False and 'pickup time' in result.get('error', '').lower(),
        f"Error: {result.get('error')}"
    )

print()

# ============================================================
# TEST CATEGORY 16: EDGE CASES
# ============================================================
print("🔍 TEST CATEGORY 16: EDGE CASES")
print("-" * 70)

# Test: Multiple identical items
clear_session()
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "2 large lamb kebabs"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("getCartState", {}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    cart_result = results[0].get('result', {})
    cart = cart_result.get('cart', [])
    test_result(
        "Add multiple identical items (quantity)",
        len(cart) > 0 and (cart[0].get('quantity', 1) == 2 or len(cart) == 2),
        f"Cart: {len(cart)} items, first item quantity: {cart[0].get('quantity', 1) if cart else 0}"
    )

# Test: All exclusions at once
clear_session()
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab no tomato no onion no pickles"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("getCartState", {}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    cart_result = results[0].get('result', {})
    cart = cart_result.get('cart', [])
    if cart:
        salads = cart[0].get('salads', [])
        test_result(
            "Multiple exclusions",
            'tomato' not in salads and 'onion' not in salads and 'pickles' not in salads,
            f"Salads: {salads}"
        )

# Test: All salads
clear_session()
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab with the lot"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("getCartState", {}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    cart_result = results[0].get('result', {})
    cart = cart_result.get('cart', [])
    if cart:
        salads = cart[0].get('salads', [])
        test_result(
            "Add 'the lot' (all salads)",
            len(salads) >= 3,
            f"Salads: {salads} ({len(salads)} items)"
        )

# Test: Clear cart
clear_session()
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "large lamb kebab"}, call_id=call_id))
call_webhook(create_vapi_webhook_payload("quickAddItem", {"description": "coke"}, call_id=call_id))
response = call_webhook(create_vapi_webhook_payload("clearCart", {}, call_id=call_id))[0]
results = response.get('results', [])
if results:
    result = results[0].get('result', {})
    # Verify cart is empty
    response2 = call_webhook(create_vapi_webhook_payload("getCartState", {}, call_id=call_id))[0]
    results2 = response2.get('results', [])
    if results2:
        cart_result = results2[0].get('result', {})
        cart = cart_result.get('cart', [])
        test_result(
            "Clear cart",
            len(cart) == 0,
            f"Cart has {len(cart)} items (expected 0)"
        )

print()

# ============================================================
# FINAL SUMMARY
# ============================================================
print("="*70)
print("TEST SUMMARY")
print("="*70)
print(f"Total tests run: {tests_run}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success rate: {(tests_passed/tests_run*100):.1f}%")
print("="*70)

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! System is functioning correctly at full capacity.")
else:
    print(f"⚠️  {tests_failed} test(s) failed. Review the failures above.")

# Save detailed report
report = {
    "timestamp": datetime.now().isoformat(),
    "summary": {
        "total": tests_run,
        "passed": tests_passed,
        "failed": tests_failed,
        "success_rate": f"{(tests_passed/tests_run*100):.1f}%"
    },
    "results": test_results
}

report_file = "test_comprehensive_report.json"
with open(report_file, 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n📄 Detailed report saved to: {report_file}")

#!/usr/bin/env python3
"""
Comprehensive test suite for ALL order scenarios
Tests EVERY type of order to prevent back-and-forth issues
"""

import sys
sys.path.insert(0, '.')

from kebabalab.server import (
    parse_salads, parse_sauces, parse_protein, parse_size, parse_quantity,
    tool_quick_add_item, tool_convert_items_to_meals, tool_price_cart,
    session_set, session_get, calculate_price, SESSIONS, app, request
)
import json

# Test counter
tests_passed = 0
tests_failed = 0
failures = []

def test(name, condition, details=""):
    """Track test results"""
    global tests_passed, tests_failed, failures
    if condition:
        tests_passed += 1
        print(f"✅ {name}")
    else:
        tests_failed += 1
        failures.append(f"❌ {name}: {details}")
        print(f"❌ {name}: {details}")

def clear_session():
    """Clear session for clean test"""
    global SESSIONS
    SESSIONS.clear()
    # Set cart directly in session
    session_id = 'test_session'
    SESSIONS[session_id] = {
        'cart': [],
        '_meta': {
            'created_at': None,
            'last_access': None
        }
    }

# Create Flask test context for all tests
test_context = app.test_request_context(json={'message': {'call': {'customer': {'number': 'test_session'}}}})
test_context.__enter__()

print("="*80)
print("COMPREHENSIVE ORDER TESTING - ALL SCENARIOS")
print("="*80)

# ========== TEST 1: EXCLUSION PARSING ==========
print("\n📋 TEST GROUP 1: EXCLUSION PARSING")
print("-" * 80)

# Salad exclusions
test("No onion parsing",
     'onion' not in parse_salads("lettuce, tomato, onion, no onion"),
     f"Got: {parse_salads('lettuce, tomato, onion, no onion')}")

test("Without pickles parsing",
     'pickles' not in parse_salads("lettuce, tomato, pickles, without pickles"),
     f"Got: {parse_salads('lettuce, tomato, pickles, without pickles')}")

test("Hold lettuce parsing",
     'lettuce' not in parse_salads("lettuce, tomato, onion, hold lettuce"),
     f"Got: {parse_salads('lettuce, tomato, onion, hold lettuce')}")

test("Multiple exclusions",
     'onion' not in parse_salads("lettuce, tomato, onion, pickles, no onion, no pickles"),
     f"Got: {parse_salads('lettuce, tomato, onion, pickles, no onion, no pickles')}")

# Sauce exclusions
test("No garlic parsing",
     'garlic' not in parse_sauces("garlic, chilli, bbq, no garlic"),
     f"Got: {parse_sauces('garlic, chilli, bbq, no garlic')}")

test("Without chilli parsing",
     'chilli' not in parse_sauces("garlic, chilli, without chilli"),
     f"Got: {parse_sauces('garlic, chilli, without chilli')}")

test("Hold bbq parsing",
     'bbq' not in parse_sauces("garlic, bbq, hold bbq"),
     f"Got: {parse_sauces('garlic, bbq, hold bbq')}")

# ========== TEST 2: BASIC QUICKADD ORDERS ==========
print("\n📋 TEST GROUP 2: BASIC QUICKADD ORDERS")
print("-" * 80)

clear_session()
result = tool_quick_add_item({'description': 'small chicken kebab with lettuce, tomato, garlic'})
test("Small chicken kebab", result['ok'] and result['item']['size'] == 'small' and result['item']['protein'] == 'chicken',
     f"Size: {result.get('item', {}).get('size')}, Protein: {result.get('item', {}).get('protein')}")
test("Small kebab price", result['item']['price'] == 10.0, f"Got: ${result['item']['price']}")

clear_session()
result = tool_quick_add_item({'description': 'large lamb kebab with lettuce, tomato, onion, garlic, chilli'})
test("Large lamb kebab", result['ok'] and result['item']['size'] == 'large' and result['item']['protein'] == 'lamb',
     f"Size: {result.get('item', {}).get('size')}, Protein: {result.get('item', {}).get('protein')}")
test("Large kebab price", result['item']['price'] == 15.0, f"Got: ${result['item']['price']}")

# ========== TEST 3: EXCLUSIONS IN QUICKADD ==========
print("\n📋 TEST GROUP 3: EXCLUSIONS IN QUICKADD")
print("-" * 80)

clear_session()
result = tool_quick_add_item({'description': 'small chicken kebab with lettuce, tomato, onion, garlic, no onion'})
test("QuickAdd with no onion",
     result['ok'] and 'onion' not in result['item']['salads'],
     f"Salads: {result.get('item', {}).get('salads')}")
test("QuickAdd keeps other salads",
     'lettuce' in result['item']['salads'] and 'tomato' in result['item']['salads'],
     f"Salads: {result.get('item', {}).get('salads')}")

clear_session()
result = tool_quick_add_item({'description': 'large lamb kebab with garlic, chilli, bbq, no garlic'})
test("QuickAdd with no garlic",
     result['ok'] and 'garlic' not in result['item']['sauces'],
     f"Sauces: {result.get('item', {}).get('sauces')}")
test("QuickAdd keeps other sauces",
     'chilli' in result['item']['sauces'] and 'bbq' in result['item']['sauces'],
     f"Sauces: {result.get('item', {}).get('sauces')}")

# ========== TEST 4: MEAL CONVERSIONS - CORRECT PRICING ==========
print("\n📋 TEST GROUP 4: MEAL CONVERSIONS - PRICING")
print("-" * 80)

# Scenario: 2 kebabs + 2 cokes, then convert to meals
clear_session()
tool_quick_add_item({'description': 'small chicken kebab with lettuce, tomato, garlic'})
tool_quick_add_item({'description': 'small chicken kebab with lettuce, tomato, garlic'})
tool_quick_add_item({'description': '2 cokes'})

cart_before = session_get('cart', [])
test("Cart has 3 items before conversion", len(cart_before) == 3,
     f"Got {len(cart_before)} items")

result = tool_convert_items_to_meals({'drinkBrand': 'coke', 'chipsSize': 'small'})
cart_after = session_get('cart', [])

test("Meal conversion successful", result['ok'], f"Error: {result.get('error')}")
test("Duplicate drinks removed", len(cart_after) == 2,  # 2 meals, cokes removed
     f"Got {len(cart_after)} items: {[item.get('name') for item in cart_after]}")

price_result = tool_price_cart({})
test("2 small kebab meals = $34", price_result['total'] == 34.0,
     f"Got: ${price_result['total']}")

# ========== TEST 5: MEAL CONVERSIONS - PARTIAL DRINKS ==========
print("\n📋 TEST GROUP 5: MEAL CONVERSIONS - PARTIAL DRINKS")
print("-" * 80)

# Scenario: 2 kebabs + 3 cokes, convert 2 to meals (should leave 1 coke)
clear_session()
tool_quick_add_item({'description': 'small chicken kebab'})
tool_quick_add_item({'description': 'small chicken kebab'})
tool_quick_add_item({'description': '3 cokes'})

tool_convert_items_to_meals({'drinkBrand': 'coke', 'chipsSize': 'small'})
cart = session_get('cart', [])

# Should have: 2 meals + 1 remaining coke
drinks_in_cart = [item for item in cart if item.get('category') == 'drinks']
test("Extra drink remains after conversion",
     len(drinks_in_cart) == 1 and drinks_in_cart[0]['quantity'] == 1,
     f"Drinks in cart: {drinks_in_cart}")

price_result = tool_price_cart({})
test("2 meals + 1 coke = $37.50", price_result['total'] == 37.50,
     f"Got: ${price_result['total']}")

# ========== TEST 6: HSP WITH CHEESE (INCLUDED) ==========
print("\n📋 TEST GROUP 6: HSP CHEESE PRICING")
print("-" * 80)

clear_session()
result = tool_quick_add_item({'description': 'small chicken hsp with cheese'})
test("Small HSP base price", result['item']['price'] == 15.0,
     f"Got: ${result['item']['price']} (cheese should be included)")
test("HSP cheese flag set", result['item']['cheese'] == True,
     f"Cheese: {result['item'].get('cheese')}")

clear_session()
result = tool_quick_add_item({'description': 'large lamb hsp with cheese'})
test("Large HSP base price", result['item']['price'] == 20.0,
     f"Got: ${result['item']['price']} (cheese should be included)")

# ========== TEST 7: COMPLEX MIXED ORDERS ==========
print("\n📋 TEST GROUP 7: COMPLEX MIXED ORDERS")
print("-" * 80)

clear_session()
tool_quick_add_item({'description': 'large chicken kebab with lettuce, tomato, garlic, no tomato'})
tool_quick_add_item({'description': 'small lamb kebab with onion, pickles, chilli, bbq'})
tool_quick_add_item({'description': 'large chicken hsp with cheese'})
tool_quick_add_item({'description': 'small chips'})
tool_quick_add_item({'description': 'coke'})

cart = session_get('cart', [])
test("Complex cart has 5 items", len(cart) == 5, f"Got {len(cart)} items")

# Verify exclusions worked
kebab1 = cart[0]
test("First kebab has no tomato", 'tomato' not in kebab1['salads'],
     f"Salads: {kebab1.get('salads')}")
test("First kebab has lettuce", 'lettuce' in kebab1['salads'],
     f"Salads: {kebab1.get('salads')}")

price_result = tool_price_cart({})
expected_total = 15.0 + 10.0 + 20.0 + 5.0 + 3.5  # $53.50
test("Complex order total correct", price_result['total'] == expected_total,
     f"Expected ${expected_total}, got ${price_result['total']}")

# ========== TEST 8: QUANTITY HANDLING ==========
print("\n📋 TEST GROUP 8: QUANTITY HANDLING")
print("-" * 80)

clear_session()
result = tool_quick_add_item({'description': '3 large chicken kebabs'})
test("Quantity parsing", result['item']['quantity'] == 3,
     f"Got quantity: {result['item']['quantity']}")

price_result = tool_price_cart({})
test("3 large kebabs = $45", price_result['total'] == 45.0,
     f"Got: ${price_result['total']}")

# ========== TEST 9: SIZE CONFIRMATION REQUIREMENT ==========
print("\n📋 TEST GROUP 9: SIZE CONFIRMATION")
print("-" * 80)

clear_session()
result = tool_quick_add_item({'description': 'chicken kebab'})  # No size
test("Missing size returns error", not result['ok'] and 'size' in result.get('error', '').lower(),
     f"Response: {result}")

# ========== TEST 10: MEAL CONVERSION - NO MATCHING DRINKS ==========
print("\n📋 TEST GROUP 10: MEAL CONVERSION - NO DRINK DUPLICATION")
print("-" * 80)

# Scenario: 2 kebabs + sprite, convert with coke (sprite should remain)
clear_session()
tool_quick_add_item({'description': 'small chicken kebab'})
tool_quick_add_item({'description': 'small chicken kebab'})
tool_quick_add_item({'description': 'sprite'})

tool_convert_items_to_meals({'drinkBrand': 'coke', 'chipsSize': 'small'})
cart = session_get('cart', [])

# Should have: 2 meals (with coke) + 1 sprite
test("Non-matching drink remains",
     any(item.get('category') == 'drinks' for item in cart),
     f"Cart: {[item.get('name') for item in cart]}")

price_result = tool_price_cart({})
test("2 coke meals + sprite = $37.50", price_result['total'] == 37.50,
     f"Got: ${price_result['total']}")

# ========== TEST 11: HSP COMBOS ==========
print("\n📋 TEST GROUP 11: HSP COMBO CONVERSIONS")
print("-" * 80)

clear_session()
tool_quick_add_item({'description': 'small chicken hsp'})
tool_quick_add_item({'description': 'coke'})

tool_convert_items_to_meals({'drinkBrand': 'coke'})
cart = session_get('cart', [])

test("HSP converted to combo", cart[0].get('is_combo') == True,
     f"is_combo: {cart[0].get('is_combo')}")
test("HSP combo has no separate drink", len(cart) == 1,
     f"Cart has {len(cart)} items")

price_result = tool_price_cart({})
test("Small HSP combo = $17", price_result['total'] == 17.0,
     f"Got: ${price_result['total']}")

# ========== TEST 12: EDGE CASE - EMPTY DESCRIPTIONS ==========
print("\n📋 TEST GROUP 12: EDGE CASES")
print("-" * 80)

clear_session()
result = tool_quick_add_item({'description': ''})
test("Empty description handled", not result['ok'],
     f"Should fail but got: {result}")

clear_session()
result = tool_quick_add_item({'description': 'xyz123'})
test("Invalid item handled", not result['ok'],
     f"Should fail but got: {result}")

# ========== FINAL REPORT ==========
print("\n" + "="*80)
print("FINAL RESULTS")
print("="*80)
print(f"✅ Tests Passed: {tests_passed}")
print(f"❌ Tests Failed: {tests_failed}")
print(f"📊 Total Tests: {tests_passed + tests_failed}")
print(f"📈 Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")

if failures:
    print("\n❌ FAILED TESTS:")
    print("-" * 80)
    for failure in failures:
        print(failure)
    print("\n🚨 SYSTEM NOT READY - FIX FAILURES ABOVE")
    sys.exit(1)
else:
    print("\n✅ ALL TESTS PASSED - SYSTEM READY FOR DEPLOYMENT")
    sys.exit(0)

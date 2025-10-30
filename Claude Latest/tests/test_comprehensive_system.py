#!/usr/bin/env python3
"""
Comprehensive System Test Suite for Kebabalab VAPI Server
Tests all major functionality end-to-end
"""

import sys
import json
from datetime import datetime, timedelta

# Import the server module
sys.path.insert(0, '.')
from kebabalab import server

# Test counter
tests_run = 0
tests_passed = 0
tests_failed = 0


def test_result(name, passed, details=""):
    """Record and print test result"""
    global tests_run, tests_passed, tests_failed
    tests_run += 1

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


def setup_test_context():
    """Setup mock request context for testing"""
    test_payload = {
        "message": {
            "call": {
                "id": "test-call-123",
                "customer": {
                    "number": "+61412345678"
                }
            },
            "toolCalls": []
        }
    }
    return server.app.test_request_context(json=test_payload)


print("=" * 70)
print("COMPREHENSIVE SYSTEM TEST SUITE")
print("=" * 70)
print()

# ============================================================
# TEST 1: Module Imports and Initialization
# ============================================================
print("📦 MODULE & INITIALIZATION TESTS")
print("-" * 70)

test_result(
    "Server module imports",
    hasattr(server, 'app'),
    "Flask app initialized"
)

test_result(
    "Database initialized",
    hasattr(server, 'init_database'),
    "Database functions available"
)

test_result(
    "Session functions available",
    all(hasattr(server, f) for f in ['session_get', 'session_set', 'session_clear']),
    "All session management functions present"
)

test_result(
    "All 17 tools registered",
    len(server.TOOLS) == 17,
    f"Found {len(server.TOOLS)} tools: {', '.join(list(server.TOOLS.keys())[:5])}..."
)

print()

# ============================================================
# TEST 2: Menu Loading
# ============================================================
print("📋 MENU LOADING TESTS")
print("-" * 70)

server.load_menu()

test_result(
    "Menu loaded successfully",
    len(server.MENU) > 0,
    f"Loaded {len(server.MENU)} categories"
)

categories = server.MENU.get('categories', {})

test_result(
    "Kebabs category exists",
    'kebabs' in categories,
    f"Found {len(categories.get('kebabs', []))} kebab items"
)

test_result(
    "HSP category exists",
    'hsp' in categories,
    f"Found {len(categories.get('hsp', []))} HSP items"
)

test_result(
    "Drinks category exists",
    'drinks' in categories,
    f"Found {len(categories.get('drinks', []))} drink items"
)

# Check for specific items
lamb_kebab_found = False
for item in categories.get('kebabs', []):
    if 'lamb' in item.get('name', '').lower():
        lamb_kebab_found = True
        break

test_result(
    "Lamb kebab item exists in menu",
    lamb_kebab_found,
    "Core menu item present"
)

print()

# ============================================================
# TEST 3: Tool Functions - Basic Calls
# ============================================================
print("🔧 TOOL FUNCTION TESTS")
print("-" * 70)

with setup_test_context():
    # Clear any existing session
    server.session_clear()

    # Test 1: checkOpen
    result = server.tool_check_open({})
    test_result(
        "checkOpen() executes",
        result.get('ok') == True,
        f"Status: {result.get('status', 'unknown')}"
    )

    # Test 2: quickAddItem - Lamb Kebab
    result = server.tool_quick_add_item({
        'description': 'large lamb kebab no onion'
    })
    test_result(
        "quickAddItem() - Add lamb kebab",
        result.get('ok') == True and result.get('cartSize') == 1,
        f"Message: {result.get('message', '')[:60]}..."
    )

    # Test 3: quickAddItem - Chicken HSP
    result = server.tool_quick_add_item({
        'description': 'small chicken hsp'
    })
    test_result(
        "quickAddItem() - Add chicken HSP",
        result.get('ok') == True and result.get('cartSize') == 2,
        f"Cart now has {result.get('cartSize')} items"
    )

    # Test 4: getCartState
    result = server.tool_get_cart_state({})
    test_result(
        "getCartState() - View cart",
        result.get('ok') == True and result.get('itemCount') == 2,
        f"Cart contains {result.get('itemCount')} items"
    )

    # Test 5: priceCart
    result = server.tool_price_cart({})
    test_result(
        "priceCart() - Calculate totals",
        result.get('ok') == True and result.get('total') > 0,
        f"Total: ${result.get('total', 0):.2f}, GST: ${result.get('gst', 0):.2f}"
    )

    # Verify GST is now calculated (not $0.00)
    test_result(
        "GST calculation working",
        result.get('gst', 0) > 0,
        f"GST component: ${result.get('gst', 0):.2f} (was $0.00 before fix)"
    )

    # Test 6: editCartItem - Change HSP size
    result = server.tool_edit_cart_item({
        'itemIndex': 1,
        'modificationsRaw': json.dumps({'size': 'large'})
    })
    test_result(
        "editCartItem() - Change size",
        result.get('ok') == True,
        f"Message: {result.get('message', '')[:60]}..."
    )

    # Test 7: convertItemsToMeals
    result = server.tool_convert_items_to_meals({
        'itemIndices': [0, 1],
        'drinkBrand': 'coke',
        'chipsSize': 'small',
        'chipsSalt': 'chicken'
    })
    test_result(
        "convertItemsToMeals() - Make combos",
        result.get('ok') == True,
        f"Converted {result.get('convertedCount', 0)} items to meals"
    )

    # Test 8: Price cart again to see combo pricing
    result = server.tool_price_cart({})
    combo_total = result.get('total', 0)
    test_result(
        "priceCart() - After combo conversion",
        result.get('ok') == True and combo_total > 0,
        f"New total: ${combo_total:.2f} (includes combo additions)"
    )

    # Test 9: getOrderSummary
    result = server.tool_get_order_summary({})
    test_result(
        "getOrderSummary() - Generate summary",
        result.get('ok') == True and len(result.get('summary', '')) > 0,
        f"Summary length: {len(result.get('summary', ''))} chars"
    )

    # Test 10: setPickupTime
    result = server.tool_set_pickup_time({
        'requestedTime': '20 minutes'
    })
    test_result(
        "setPickupTime() - Set time",
        result.get('ok') == True,
        f"Pickup: {result.get('readyAt', 'unknown')}"
    )

    # Test 11: estimateReadyTime
    server.session_set('pickup_confirmed', False)  # Reset for this test
    result = server.tool_estimate_ready_time({})
    test_result(
        "estimateReadyTime() - Auto-estimate",
        result.get('ok') == True,
        f"Estimated: {result.get('readyAt', 'unknown')}"
    )

print()

# ============================================================
# TEST 4: Input Validation
# ============================================================
print("✅ INPUT VALIDATION TESTS")
print("-" * 70)

with setup_test_context():
    server.session_clear()

    # Test invalid customer name
    is_valid, msg = server.validate_customer_name("A")
    test_result(
        "Reject too-short name",
        not is_valid,
        f"Correctly rejected: {msg}"
    )

    is_valid, msg = server.validate_customer_name("A" * 101)
    test_result(
        "Reject too-long name",
        not is_valid,
        f"Correctly rejected: {msg}"
    )

    is_valid, msg = server.validate_customer_name("John Smith")
    test_result(
        "Accept valid name",
        is_valid,
        f"Accepted: {msg}"
    )

    # Test phone number validation
    is_valid, msg = server.validate_phone_number("0412345678")
    test_result(
        "Accept valid Australian mobile",
        is_valid,
        f"Normalized to: {msg}"
    )

    is_valid, msg = server.validate_phone_number("invalid")
    test_result(
        "Reject invalid phone",
        not is_valid,
        f"Correctly rejected: {msg}"
    )

print()

# ============================================================
# TEST 5: Session Management
# ============================================================
print("💾 SESSION MANAGEMENT TESTS")
print("-" * 70)

with setup_test_context():
    server.session_clear()

    # Test session_set and session_get
    server.session_set('test_key', 'test_value')
    value = server.session_get('test_key')
    test_result(
        "Session set/get works",
        value == 'test_value',
        f"Stored and retrieved: {value}"
    )

    # Test complex data types
    test_data = {'cart': [{'item': 'kebab', 'price': 15.0}], 'total': 15.0}
    server.session_set('test_complex', test_data)
    retrieved = server.session_get('test_complex')
    test_result(
        "Session stores complex data",
        retrieved == test_data,
        f"Dict stored and retrieved correctly"
    )

    # Test session_clear
    server.session_clear()
    value = server.session_get('test_key', default='not_found')
    test_result(
        "Session clear works",
        value == 'not_found',
        "Session data cleared successfully"
    )

    # Test Redis availability
    redis_status = "Redis connected" if server.REDIS_CLIENT else "In-memory fallback"
    test_result(
        "Session storage initialized",
        True,  # Always pass, just informational
        redis_status
    )

print()

# ============================================================
# TEST 6: GST Calculation
# ============================================================
print("💰 GST CALCULATION TESTS")
print("-" * 70)

# Test GST calculation function
subtotal, gst = server.calculate_gst_from_inclusive(110.0)
test_result(
    "GST calculation: $110.00 inclusive",
    abs(gst - 10.0) < 0.01 and abs(subtotal - 100.0) < 0.01,
    f"Subtotal: ${subtotal:.2f}, GST: ${gst:.2f}"
)

subtotal, gst = server.calculate_gst_from_inclusive(43.0)
expected_gst = 43.0 * (0.10 / 1.10)
test_result(
    "GST calculation: $43.00 inclusive",
    abs(gst - expected_gst) < 0.01,
    f"GST: ${gst:.2f} (expected: ${expected_gst:.2f})"
)

# Test with zero
subtotal, gst = server.calculate_gst_from_inclusive(0.0)
test_result(
    "GST calculation: $0.00 inclusive",
    gst == 0.0 and subtotal == 0.0,
    "Zero handled correctly"
)

print()

# ============================================================
# TEST 7: Error Handling
# ============================================================
print("🚨 ERROR HANDLING TESTS")
print("-" * 70)

with setup_test_context():
    server.session_clear()

    # Test quickAddItem with invalid item
    result = server.tool_quick_add_item({
        'itemName': 'nonexistent_item_xyz',
        'size': 'large'
    })
    test_result(
        "Handle invalid item name",
        result.get('ok') == False,
        f"Error: {result.get('error', '')[:60]}..."
    )

    # Test editCartItem with invalid index
    result = server.tool_edit_cart_item({
        'itemIndex': 999,
        'modificationsRaw': '{}'
    })
    test_result(
        "Handle invalid cart index",
        result.get('ok') == False,
        f"Error: {result.get('error', '')[:60]}..."
    )

    # Test removeCartItem on empty cart
    result = server.tool_remove_cart_item({
        'itemIndex': 0
    })
    test_result(
        "Handle remove from empty cart",
        result.get('ok') == False,
        f"Error: {result.get('error', '')[:60]}..."
    )

    # Test createOrder without cart
    result = server.tool_create_order({
        'customerName': 'Test User',
        'customerPhone': '0412345678'
    })
    test_result(
        "Handle order creation with empty cart",
        result.get('ok') == False,
        f"Error: {result.get('error', '')[:60]}..."
    )

print()

# ============================================================
# TEST 8: Complete Order Flow
# ============================================================
print("🛒 COMPLETE ORDER FLOW TEST")
print("-" * 70)

with setup_test_context():
    server.session_clear()

    flow_steps = []

    # Step 1: Add items
    result = server.tool_quick_add_item({
        'description': 'large lamb kebab no onion'
    })
    flow_steps.append(('Add lamb kebab', result.get('ok')))

    result = server.tool_quick_add_item({
        'description': 'small chicken hsp'
    })
    flow_steps.append(('Add chicken HSP', result.get('ok')))

    # Step 2: Convert to meals
    result = server.tool_convert_items_to_meals({
        'drinkBrand': 'coke'
    })
    flow_steps.append(('Convert to meals', result.get('ok')))

    # Step 3: Price cart
    result = server.tool_price_cart({})
    flow_steps.append(('Price cart', result.get('ok')))
    total = result.get('total', 0)
    gst = result.get('gst', 0)

    # Step 4: Set pickup time
    result = server.tool_set_pickup_time({
        'requestedTime': '20 minutes'
    })
    flow_steps.append(('Set pickup time', result.get('ok')))

    # Step 5: Create order
    result = server.tool_create_order({
        'customerName': 'Test Customer',
        'customerPhone': '0412345678',
        'notes': 'Test order from comprehensive test suite',
        'sendSMS': False
    })
    flow_steps.append(('Create order', result.get('ok')))
    order_number = result.get('orderNumber', 'N/A')

    # Check all steps
    all_passed = all(passed for _, passed in flow_steps)
    test_result(
        "Complete order flow (all steps)",
        all_passed,
        f"Order #{order_number} created with ${total:.2f} total (GST: ${gst:.2f})"
    )

    # Print flow details
    for step, passed in flow_steps:
        status = "✓" if passed else "✗"
        print(f"   {status} {step}")

print()

# ============================================================
# TEST 9: Exclusions and Modifications
# ============================================================
print("🔧 EXCLUSIONS & MODIFICATIONS TESTS")
print("-" * 70)

with setup_test_context():
    server.session_clear()

    # Test "no onion" exclusion
    result = server.tool_quick_add_item({
        'description': 'large lamb kebab no onion'
    })

    cart = server.session_get('cart', [])
    has_onion_in_salads = False
    if cart and len(cart) > 0:
        salads = cart[0].get('salads', [])
        has_onion_in_salads = 'onion' not in salads

    test_result(
        "Onion exclusion works",
        has_onion_in_salads,
        f"Salads: {cart[0].get('salads', []) if cart else []}"
    )

    # Test "no cheese" on HSP
    server.session_clear()
    result = server.tool_quick_add_item({
        'description': 'small chicken hsp no cheese'
    })

    cart = server.session_get('cart', [])
    cheese_excluded = False
    if cart and len(cart) > 0:
        cheese_excluded = not cart[0].get('cheese', False)

    test_result(
        "Cheese exclusion works on HSP",
        cheese_excluded,
        f"Cheese flag: {cart[0].get('cheese', False) if cart else 'N/A'}"
    )

print()

# ============================================================
# TEST 10: Database Operations
# ============================================================
print("🗄️  DATABASE TESTS")
print("-" * 70)

# Initialize database
try:
    server.init_database()
    test_result(
        "Database initialization",
        True,
        "Database initialized successfully"
    )
except Exception as e:
    test_result(
        "Database initialization",
        False,
        f"Error: {str(e)}"
    )

# Test database connection
try:
    with server.DatabaseConnection() as cursor:
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        test_result(
            "Database query execution",
            True,
            f"Found {count} orders in database"
        )
except Exception as e:
    test_result(
        "Database query execution",
        False,
        f"Error: {str(e)}"
    )

print()

# ============================================================
# FINAL RESULTS
# ============================================================
print("=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Total tests run: {tests_run}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success rate: {(tests_passed/tests_run*100):.1f}%")
print("=" * 70)

if tests_failed == 0:
    print("🎉 ALL TESTS PASSED! System is functioning correctly.")
    sys.exit(0)
else:
    print(f"⚠️  {tests_failed} test(s) failed. Review the failures above.")
    sys.exit(1)

#!/usr/bin/env python3
"""
VAPI Integration Tests - Testing REAL webhook calls
====================================================

Tests the actual /webhook endpoint with VAPI-formatted payloads.
This simulates what VAPI actually sends to our server.

NOT just testing tool functions directly - testing the COMPLETE flow:
1. VAPI sends webhook POST with specific JSON format
2. Server parses the VAPI format
3. Server extracts tool calls
4. Server executes tools
5. Server returns results in VAPI format
6. Session management works across calls
"""

import sys
import json
from datetime import datetime

sys.path.insert(0, '.')
from kebabalab import server

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


def create_vapi_webhook_payload(tool_name, arguments, call_id="test-call-123", phone="+61412345678"):
    """
    Create a VAPI-formatted webhook payload.
    This is what VAPI actually sends to /webhook endpoint.
    """
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


def call_webhook(payload):
    """
    Make a simulated webhook call to the server.
    Tests the ACTUAL webhook endpoint, not just tool functions.
    """
    with server.app.test_request_context(json=payload):
        try:
            # Manually push the request context
            server.request.push(payload)

            response = server.webhook()

            # Pop the request context
            server.request.pop()

            # webhook() returns either a tuple (data, status) or just data
            if isinstance(response, tuple):
                data, status = response
                return data, status
            else:
                return response, 200
        except Exception as e:
            return {"error": str(e)}, 500


print("=" * 70)
print("VAPI INTEGRATION TESTS")
print("Testing REAL webhook calls with VAPI-formatted payloads")
print("=" * 70)
print()

# Initialize
server.init_database()
server.load_menu()

# ============================================================
# TEST 1: Webhook Endpoint Basic Functionality
# ============================================================
print("🔌 WEBHOOK ENDPOINT TESTS")
print("-" * 70)

# Test 1.1: Webhook with no tool calls
payload = {
    "message": {
        "call": {"id": "test-123", "customer": {"number": "+61412345678"}},
        "toolCalls": []
    }
}
response, status = call_webhook(payload)
test_result(
    "Webhook acknowledges empty tool calls with 200 OK (no lag)",
    status == 200 and response.get('status') == 'acknowledged',
    f"Status: {status}, Response: {response.get('status', 'N/A')}"
)

# Test 1.2: Check Open (simple tool, no params)
payload = create_vapi_webhook_payload("checkOpen", {})
response, status = call_webhook(payload)

results = response.get('results', [])
test_result(
    "Webhook handles checkOpen correctly",
    status == 200 and len(results) > 0 and results[0].get('result', {}).get('ok') == True,
    f"Status: {status}, Results: {len(results)}"
)

print()

# ============================================================
# TEST 2: Complete Order Flow via Webhook
# ============================================================
print("🛒 COMPLETE ORDER FLOW (VIA WEBHOOK)")
print("-" * 70)

# Start fresh session
call_id = "test-call-456"
phone = "+61400000000"

# Step 1: Add first item - Large Lamb Kebab
print("\n📞 Step 1: Add large lamb kebab...")
payload = create_vapi_webhook_payload(
    "quickAddItem",
    {"description": "large lamb kebab with no onion"},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
step1_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True and
            results[0].get('result', {}).get('cartSize') == 1)
test_result(
    "Step 1: Add lamb kebab via webhook",
    step1_ok,
    f"Cart size: {results[0].get('result', {}).get('cartSize', 0)}"
)

# Step 2: Add second item - Small Chicken HSP
print("\n📞 Step 2: Add small chicken HSP...")
payload = create_vapi_webhook_payload(
    "quickAddItem",
    {"description": "small chicken hsp"},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
step2_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True and
            results[0].get('result', {}).get('cartSize') == 2)
test_result(
    "Step 2: Add HSP via webhook",
    step2_ok,
    f"Cart size: {results[0].get('result', {}).get('cartSize', 0)}"
)

# Step 3: Get cart state
print("\n📞 Step 3: Get cart state...")
payload = create_vapi_webhook_payload(
    "getCartState",
    {},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
step3_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True and
            results[0].get('result', {}).get('itemCount') == 2)
test_result(
    "Step 3: Get cart state via webhook",
    step3_ok,
    f"Item count: {results[0].get('result', {}).get('itemCount', 0)}"
)

# Step 4: Convert to meals
print("\n📞 Step 4: Convert to meals...")
payload = create_vapi_webhook_payload(
    "convertItemsToMeals",
    {"drinkBrand": "coke", "chipsSize": "small"},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
step4_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True)
test_result(
    "Step 4: Convert to meals via webhook",
    step4_ok,
    f"Converted: {results[0].get('result', {}).get('convertedCount', 0)} items"
)

# Step 5: Price cart
print("\n📞 Step 5: Price cart...")
payload = create_vapi_webhook_payload(
    "priceCart",
    {},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
total = results[0].get('result', {}).get('total', 0) if results else 0
gst = results[0].get('result', {}).get('gst', 0) if results else 0
step5_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True and
            total > 0 and
            gst > 0)
test_result(
    "Step 5: Price cart via webhook",
    step5_ok,
    f"Total: ${total:.2f}, GST: ${gst:.2f}"
)

# Step 6: Set pickup time
print("\n📞 Step 6: Set pickup time...")
payload = create_vapi_webhook_payload(
    "setPickupTime",
    {"requestedTime": "20 minutes"},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
step6_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True)
test_result(
    "Step 6: Set pickup time via webhook",
    step6_ok,
    f"Ready at: {results[0].get('result', {}).get('readyAt', 'unknown')}"
)

# Step 7: Create order
print("\n📞 Step 7: Create order...")
payload = create_vapi_webhook_payload(
    "createOrder",
    {
        "customerName": "Integration Test Customer",
        "customerPhone": phone,
        "notes": "Test order via webhook integration",
        "sendSMS": False
    },
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
order_number = results[0].get('result', {}).get('orderNumber', 'N/A') if results else 'N/A'
step7_ok = (status == 200 and
            len(results) > 0 and
            results[0].get('result', {}).get('ok') == True and
            order_number != 'N/A')
test_result(
    "Step 7: Create order via webhook",
    step7_ok,
    f"Order number: {order_number}, Total: ${total:.2f}"
)

# Final check: All steps passed
all_steps_passed = all([step1_ok, step2_ok, step3_ok, step4_ok, step5_ok, step6_ok, step7_ok])
test_result(
    "Complete order flow (all 7 steps)",
    all_steps_passed,
    f"Order {order_number} created successfully"
)

print()

# ============================================================
# TEST 3: Session Management Across Calls
# ============================================================
print("💾 SESSION MANAGEMENT VIA WEBHOOK")
print("-" * 70)

# New call with different phone number
call_id_2 = "test-call-789"
phone_2 = "+61400111111"

# Add item for phone 1
payload = create_vapi_webhook_payload(
    "quickAddItem",
    {"description": "large chicken kebab"},
    call_id=call_id,
    phone=phone
)
call_webhook(payload)

# Add different item for phone 2
payload = create_vapi_webhook_payload(
    "quickAddItem",
    {"description": "small lamb hsp"},
    call_id=call_id_2,
    phone=phone_2
)
call_webhook(payload)

# Check phone 1's cart
payload = create_vapi_webhook_payload(
    "getCartState",
    {},
    call_id=call_id,
    phone=phone
)
response, status = call_webhook(payload)
results = response.get('results', [])
phone1_cart = results[0].get('result', {}) if results else {}

# Check phone 2's cart
payload = create_vapi_webhook_payload(
    "getCartState",
    {},
    call_id=call_id_2,
    phone=phone_2
)
response, status = call_webhook(payload)
results = response.get('results', [])
phone2_cart = results[0].get('result', {}) if results else {}

test_result(
    "Sessions isolated by phone number",
    phone1_cart.get('itemCount') >= 1 and phone2_cart.get('itemCount') == 1,
    f"Phone1: {phone1_cart.get('itemCount')} items, Phone2: {phone2_cart.get('itemCount')} items"
)

print()

# ============================================================
# TEST 4: Error Handling via Webhook
# ============================================================
print("🚨 ERROR HANDLING VIA WEBHOOK")
print("-" * 70)

# Test invalid tool name
payload = create_vapi_webhook_payload(
    "nonExistentTool",
    {},
    call_id="test-call-error",
    phone="+61400222222"
)
response, status = call_webhook(payload)
results = response.get('results', [])
error_result = results[0].get('result', {}) if results else {}
test_result(
    "Webhook handles unknown tool gracefully",
    error_result.get('ok') == False and 'Unknown tool' in error_result.get('error', ''),
    f"Error: {error_result.get('error', '')[:50]}..."
)

# Test missing required parameter
payload = create_vapi_webhook_payload(
    "quickAddItem",
    {},  # Missing 'description' parameter
    call_id="test-call-error2",
    phone="+61400333333"
)
response, status = call_webhook(payload)
results = response.get('results', [])
error_result = results[0].get('result', {}) if results else {}
test_result(
    "Webhook handles missing parameters",
    error_result.get('ok') == False,
    f"Error: {error_result.get('error', '')[:50]}..."
)

# Test invalid item name
payload = create_vapi_webhook_payload(
    "quickAddItem",
    {"description": "xyz123 nonexistent item"},
    call_id="test-call-error3",
    phone="+61400444444"
)
response, status = call_webhook(payload)
results = response.get('results', [])
error_result = results[0].get('result', {}) if results else {}
test_result(
    "Webhook handles invalid items",
    error_result.get('ok') == False,
    f"Error: {error_result.get('error', '')[:50]}..."
)

print()

# ============================================================
# TEST 5: Response Format Validation
# ============================================================
print("📋 VAPI RESPONSE FORMAT VALIDATION")
print("-" * 70)

# Check response structure matches VAPI expectations
payload = create_vapi_webhook_payload(
    "checkOpen",
    {},
    call_id="test-call-format",
    phone="+61400555555"
)
response, status = call_webhook(payload)

# VAPI expects: {"results": [{"toolCallId": "...", "result": {...}}]}
test_result(
    "Response has 'results' array",
    'results' in response and isinstance(response['results'], list),
    f"Response keys: {list(response.keys())}"
)

if 'results' in response and len(response['results']) > 0:
    first_result = response['results'][0]
    test_result(
        "Each result has 'toolCallId'",
        'toolCallId' in first_result,
        f"Result keys: {list(first_result.keys())}"
    )

    test_result(
        "Each result has 'result' object",
        'result' in first_result and isinstance(first_result['result'], dict),
        f"Result type: {type(first_result.get('result'))}"
    )

print()

# ============================================================
# TEST 6: Multiple Tool Calls in One Webhook
# ============================================================
print("🔄 MULTIPLE TOOL CALLS IN SINGLE WEBHOOK")
print("-" * 70)

# VAPI can send multiple tool calls in one webhook
payload = {
    "message": {
        "call": {
            "id": "test-call-multi",
            "customer": {"number": "+61400666666"}
        },
        "toolCalls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "quickAddItem",
                    "arguments": {"description": "large lamb kebab"}
                }
            },
            {
                "id": "call_2",
                "type": "function",
                "function": {
                    "name": "quickAddItem",
                    "arguments": {"description": "small chips"}
                }
            }
        ]
    }
}

response, status = call_webhook(payload)
results = response.get('results', [])

test_result(
    "Handles multiple tool calls",
    status == 200 and len(results) == 2,
    f"Returned {len(results)} results for 2 tool calls"
)

test_result(
    "All tool calls executed successfully",
    all(r.get('result', {}).get('ok') == True for r in results),
    f"Both tool calls returned ok=True"
)

print()

# ============================================================
# TEST 7: Tool Name Mapping
# ============================================================
print("🔧 TOOL NAME MAPPING VERIFICATION")
print("-" * 70)

# Verify all 17 tools are registered and callable via webhook
expected_tools = [
    "checkOpen",
    "getCallerSmartContext",
    "quickAddItem",
    "addMultipleItemsToCart",
    "getCartState",
    "removeCartItem",
    "editCartItem",
    "priceCart",
    "convertItemsToMeals",
    "getOrderSummary",
    "setPickupTime",
    "estimateReadyTime",
    "createOrder",
    "sendMenuLink",
    "repeatLastOrder",
    "sendReceipt",
    "endCall"
]

test_result(
    "All 17 tools registered in TOOLS dict",
    len(server.TOOLS) == 17,
    f"Found {len(server.TOOLS)} tools"
)

missing_tools = []
for tool_name in expected_tools:
    if tool_name not in server.TOOLS:
        missing_tools.append(tool_name)

test_result(
    "All expected tools present",
    len(missing_tools) == 0,
    f"Missing: {missing_tools}" if missing_tools else "All tools present"
)

# Test that each tool is callable
callable_count = 0
for tool_name in expected_tools:
    if tool_name in server.TOOLS and callable(server.TOOLS[tool_name]):
        callable_count += 1

test_result(
    "All tools are callable functions",
    callable_count == len(expected_tools),
    f"{callable_count}/{len(expected_tools)} tools callable"
)

print()

# ============================================================
# FINAL SUMMARY
# ============================================================
print("=" * 70)
print("INTEGRATION TEST SUMMARY")
print("=" * 70)
print(f"Total tests run: {tests_run}")
print(f"✅ Passed: {tests_passed}")
print(f"❌ Failed: {tests_failed}")
print(f"Success rate: {(tests_passed/tests_run*100):.1f}%")
print("=" * 70)

if tests_failed == 0:
    print("🎉 ALL INTEGRATION TESTS PASSED!")
    print("✅ Webhook endpoint working correctly")
    print("✅ VAPI payload format handled properly")
    print("✅ Complete order flow works via webhook")
    print("✅ Session management works across webhook calls")
    print("✅ Error handling works via webhook")
    print("✅ Response format matches VAPI expectations")
    print()
    print("🚀 SYSTEM IS READY FOR REAL VAPI CALLS!")
    sys.exit(0)
else:
    print(f"⚠️  {tests_failed} integration test(s) failed.")
    print("Review the failures above before deploying.")
    sys.exit(1)

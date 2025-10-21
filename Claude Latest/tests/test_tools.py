"""
Test script for VAPI tools - Test without making phone calls!
Run this to test all tools and simulate a complete order flow
"""

import requests
import json
from datetime import datetime

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhook"  # Change if different
TEST_PHONE = "+61426499209"  # Test phone number

def call_tool(tool_name, parameters=None):
    """Simulate VAPI calling a tool"""
    if parameters is None:
        parameters = {}

    payload = {
        "message": {
            "toolCalls": [{
                "function": {
                    "name": tool_name,
                    "arguments": parameters
                },
                "id": f"test_{tool_name}_{datetime.now().timestamp()}"
            }]
        },
        "call": {
            "customer": {
                "number": TEST_PHONE
            }
        }
    }

    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"Parameters: {json.dumps(parameters, indent=2)}")
    print(f"{'='*60}")

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)

        if response.status_code == 200:
            result = response.json()
            print(f"✓ SUCCESS")
            print(f"Response: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"✗ FAILED - Status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        return None

def test_all_tools():
    """Test all tools in sequence"""

    print("\n" + "="*60)
    print("KEBABALAB TOOL TESTING SCRIPT")
    print("="*60)

    # Test 1: Check if open
    print("\n## TEST 1: Check if shop is open")
    call_tool("checkOpen")

    # Test 2: Get caller info
    print("\n## TEST 2: Get caller information")
    caller_info = call_tool("getCallerInfo")

    # Test 3: Start configuring a kebab
    print("\n## TEST 3: Start kebab configuration")
    call_tool("startItemConfiguration", {
        "category": "kebabs",
        "name": "Chicken Kebab"
    })

    # Test 4: Set properties
    print("\n## TEST 4: Set item properties")
    call_tool("setItemProperty", {
        "field": "size",
        "value": "small"
    })

    call_tool("setItemProperty", {
        "field": "protein",
        "value": "chicken"
    })

    call_tool("setItemProperty", {
        "field": "salads",
        "value": ["lettuce", "tomato", "onion"]
    })

    call_tool("setItemProperty", {
        "field": "sauces",
        "value": ["garlic", "chilli"]
    })

    call_tool("setItemProperty", {
        "field": "extras",
        "value": []
    })

    # Test 5: Add to cart
    print("\n## TEST 5: Add kebab to cart")
    add_result = call_tool("addItemToCart")

    # Test 6: Get cart state
    print("\n## TEST 6: Get cart state")
    call_tool("getCartState")

    # Test 7: Add chips
    print("\n## TEST 7: Add chips")
    call_tool("startItemConfiguration", {
        "category": "chips"
    })
    call_tool("setItemProperty", {
        "field": "size",
        "value": "small"
    })
    call_tool("addItemToCart")

    # Test 8: Add drink (should trigger combo!)
    print("\n## TEST 8: Add drink (should detect combo!)")
    call_tool("startItemConfiguration", {
        "category": "drinks",
        "name": "Soft Drink Can (375ml)"
    })
    call_tool("setItemProperty", {
        "field": "brand",
        "value": "coca-cola"
    })
    combo_result = call_tool("addItemToCart")

    # Check if combo was detected
    if combo_result and "results" in combo_result:
        tool_result = combo_result["results"][0]["result"]
        if tool_result.get("comboDetected"):
            print(f"\n✓✓✓ COMBO DETECTED: {tool_result['comboInfo']['name']}")
            print(f"    Savings: ${tool_result['comboInfo']['savings']}")
        else:
            print(f"\n✗✗✗ COMBO NOT DETECTED (Expected combo!)")

    # Test 9: Price cart
    print("\n## TEST 9: Price the cart")
    price_result = call_tool("priceCart")

    # Test 10: Estimate ready time
    print("\n## TEST 10: Estimate ready time")
    time_result = call_tool("estimateReadyTime")

    # Test 11: Create order
    print("\n## TEST 11: Create order")

    if price_result and time_result:
        # Extract needed info
        ready_at_iso = None
        if "results" in time_result:
            ready_at_iso = time_result["results"][0]["result"].get("readyAtIso")

        phone = TEST_PHONE
        if caller_info and "results" in caller_info:
            phone = caller_info["results"][0]["result"].get("phoneNumber", TEST_PHONE)

        if ready_at_iso:
            order_result = call_tool("createOrder", {
                "customerName": "Test Customer",
                "customerPhone": phone,
                "readyAtIso": ready_at_iso
            })

            if order_result and "results" in order_result:
                order_id = order_result["results"][0]["result"].get("orderId")
                if order_id:
                    print(f"\n✓✓✓ ORDER CREATED: #{order_id}")

    # Test 12: End call
    print("\n## TEST 12: End call")
    call_tool("endCall")

    print("\n" + "="*60)
    print("TESTING COMPLETE!")
    print("="*60)

def test_scenario_small_kebab_meal():
    """Test the exact scenario from the transcript"""

    print("\n" + "="*60)
    print("SCENARIO TEST: Small Chicken Kebab Meal")
    print("="*60)

    # Customer says: "Small chicken kebab"
    print("\n>>> Customer: Small chicken kebab")

    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})

    print("\n>>> Assistant: What salads?")
    print(">>> Customer: Lettuce, tomato, onion")

    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion"]})

    print("\n>>> Assistant: Which sauces?")
    print(">>> Customer: Garlic, chilli")

    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("addItemToCart")

    print("\n>>> Assistant: Got it! Anything else?")
    print(">>> Customer: Make it a meal with a Coke")

    # Add chips
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("addItemToCart")

    # Add drink - should trigger combo!
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "coca-cola"})
    result = call_tool("addItemToCart")

    # Check combo
    if result and "results" in result:
        tool_result = result["results"][0]["result"]
        if tool_result.get("comboDetected"):
            print(f"\n✓ CORRECT: Combo detected - {tool_result['comboInfo']['name']}")
        else:
            print(f"\n✗ ERROR: Combo should have been detected!")

    # Price and finish
    price_result = call_tool("priceCart")
    if price_result and "results" in price_result:
        total = price_result["results"][0]["result"]["totals"]["grand_total"]
        print(f"\n>>> Assistant: Your total is ${total}")
        if total == 17.0:
            print("✓ CORRECT: Price is $17 for Small Kebab Meal")
        else:
            print(f"✗ ERROR: Expected $17, got ${total}")

def test_performance():
    """Test tool performance"""
    import time

    print("\n" + "="*60)
    print("PERFORMANCE TEST")
    print("="*60)

    tests = [
        ("checkOpen", {}),
        ("getCallerInfo", {}),
        ("startItemConfiguration", {"category": "kebabs"}),
        ("setItemProperty", {"field": "size", "value": "small"}),
        ("addItemToCart", {}),
    ]

    for tool_name, params in tests:
        start = time.time()
        call_tool(tool_name, params)
        elapsed = (time.time() - start) * 1000

        if elapsed < 100:
            status = "✓ EXCELLENT"
            color = "green"
        elif elapsed < 300:
            status = "✓ GOOD"
            color = "yellow"
        elif elapsed < 500:
            status = "⚠ ACCEPTABLE"
            color = "yellow"
        else:
            status = "✗ TOO SLOW"
            color = "red"

        print(f"{tool_name}: {elapsed:.0f}ms - {status}")

    print(f"\nTarget: < 100ms per tool for instant response")
    print(f"Acceptable: < 500ms")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]

        if mode == "all":
            test_all_tools()
        elif mode == "scenario":
            test_scenario_small_kebab_meal()
        elif mode == "perf":
            test_performance()
        else:
            print("Usage: python test_tools.py [all|scenario|perf]")
            print("  all      - Test all tools in sequence")
            print("  scenario - Test the small kebab meal scenario")
            print("  perf     - Test tool performance")
    else:
        # Default: run scenario test
        test_scenario_small_kebab_meal()
        print("\n\nRun with 'all', 'scenario', or 'perf' for different tests")

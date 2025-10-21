"""
Test Cart Modification Tools - NEW in v3
Tests removeCartItem, editCartItem, clearCart
"""

import requests
import json
from datetime import datetime

WEBHOOK_URL = "http://localhost:8000/webhook"
TEST_PHONE = "+61426499209"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def call_tool(tool_name, parameters=None):
    """Call a tool and return result"""
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

    response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
    if response.status_code == 200:
        result = response.json()
        return result["results"][0]["result"] if "results" in result else {}
    return {}

def test_cart_modifications():
    """Test all cart modification tools"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}CART MODIFICATION TOOLS TEST{Colors.RESET}")
    print("="*80)

    # Setup: Add 3 items to cart
    print(f"\n{Colors.CYAN}Setup: Adding 3 items to cart...{Colors.RESET}")

    # Item 1: Small chicken kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": json.dumps(["lettuce", "tomato", "onion"])})
    call_tool("setItemProperty", {"field": "sauces", "value": json.dumps(["garlic", "chilli"])})
    call_tool("addItemToCart")

    # Item 2: Large lamb HSP
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "sauces", "value": json.dumps(["garlic", "chilli", "bbq"])})
    call_tool("setItemProperty", {"field": "cheese", "value": "true"})
    call_tool("addItemToCart")

    # Item 3: Small chips
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("addItemToCart")

    # Check cart
    cart_result = call_tool("getCartState")
    cart = cart_result.get("cart", [])
    print(f"  {Colors.GREEN}✓{Colors.RESET} Cart has {len(cart)} items")

    # TEST 1: Edit Cart Item (remove onion from first kebab)
    print(f"\n{Colors.BOLD}TEST 1: editCartItem - Remove onion from first kebab{Colors.RESET}")
    result = call_tool("editCartItem", {
        "itemIndex": 0,
        "field": "salads",
        "value": json.dumps(["lettuce", "tomato"])
    })

    if result.get("ok"):
        updated_item = result.get("updatedItem", {})
        salads = updated_item.get("salads", [])
        if "onion" not in salads and len(salads) == 2:
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - Onion removed, salads now: {salads}")
        else:
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Salads: {salads}")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Error: {result.get('error')}")

    # TEST 2: Edit Cart Item (change salt on chips)
    print(f"\n{Colors.BOLD}TEST 2: editCartItem - Change chips salt to 'none'{Colors.RESET}")
    result = call_tool("editCartItem", {
        "itemIndex": 2,
        "field": "salt_type",
        "value": "none"
    })

    if result.get("ok"):
        updated_item = result.get("updatedItem", {})
        salt_type = updated_item.get("salt_type")
        if salt_type == "none":
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - Salt changed to 'none'")
        else:
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Salt is: {salt_type}")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Error: {result.get('error')}")

    # TEST 3: Remove Cart Item (remove HSP - index 1)
    print(f"\n{Colors.BOLD}TEST 3: removeCartItem - Remove HSP (index 1){Colors.RESET}")
    result = call_tool("removeCartItem", {"itemIndex": 1})

    if result.get("ok"):
        cart_count = result.get("cartItemCount")
        if cart_count == 2:
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - HSP removed, {cart_count} items remaining")
        else:
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Cart has {cart_count} items (expected 2)")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Error: {result.get('error')}")

    # Verify cart state
    cart_result = call_tool("getCartState")
    cart = cart_result.get("cart", [])
    print(f"  Cart now has: {len(cart)} items")
    for i, item in enumerate(cart):
        cat = item.get("category", "unknown")
        print(f"    [{i}] {cat}")

    # TEST 4: Clear Cart
    print(f"\n{Colors.BOLD}TEST 4: clearCart - Clear entire cart{Colors.RESET}")
    result = call_tool("clearCart")

    if result.get("ok"):
        items_cleared = result.get("itemsCleared")
        print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - Cleared {items_cleared} items")

        # Verify cart is empty
        cart_result = call_tool("getCartState")
        cart = cart_result.get("cart", [])
        if len(cart) == 0:
            print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - Cart is now empty")
        else:
            print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Cart still has {len(cart)} items")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Error: {result.get('error')}")

    # TEST 5: Edit non-existent item (should fail)
    print(f"\n{Colors.BOLD}TEST 5: editCartItem - Try to edit non-existent item (should fail){Colors.RESET}")
    result = call_tool("editCartItem", {
        "itemIndex": 99,
        "field": "salads",
        "value": json.dumps(["lettuce"])
    })

    if not result.get("ok"):
        print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - Correctly rejected: {result.get('error')}")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Should have failed but didn't")

    # TEST 6: Remove from empty cart (should fail)
    print(f"\n{Colors.BOLD}TEST 6: removeCartItem - Try to remove from empty cart (should fail){Colors.RESET}")
    result = call_tool("removeCartItem", {"itemIndex": 0})

    if not result.get("ok"):
        print(f"  {Colors.GREEN}✓ PASS{Colors.RESET} - Correctly rejected: {result.get('error')}")
    else:
        print(f"  {Colors.RED}✗ FAIL{Colors.RESET} - Should have failed but didn't")

    print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
    print(f"{Colors.GREEN}Cart Modification Tools Test Complete!{Colors.RESET}\n")

if __name__ == "__main__":
    test_cart_modifications()

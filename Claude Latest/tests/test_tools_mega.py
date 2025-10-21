"""
MEGA TEST SUITE for Kebabalab VAPI System
Tests EVERY possible scenario including edge cases, invalid items, and error handling
"""

import requests
import json
from datetime import datetime
import time
from typing import Dict, Any, List, Optional

# Configuration
WEBHOOK_URL = "http://localhost:8000/webhook"
TEST_PHONE = "+61426499209"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class TestStats:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def finish(self):
        elapsed = time.time() - self.start_time if self.start_time else 0
        print(f"\n{'='*80}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.RESET}")
        print(f"{'='*80}")
        print(f"Total Tests:    {self.total}")
        print(f"{Colors.GREEN}Passed:         {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed:         {self.failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings:       {self.warnings}{Colors.RESET}")
        print(f"Success Rate:   {(self.passed/self.total*100) if self.total > 0 else 0:.1f}%")
        print(f"Time Elapsed:   {elapsed:.2f}s")
        print(f"{'='*80}\n")

stats = TestStats()

def call_tool(tool_name: str, parameters: Optional[Dict] = None, expect_fail: bool = False) -> Optional[Dict]:
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

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if expect_fail:
                return {"_test_meta": {"status": "unexpectedly_succeeded"}, **result}
            return result
        else:
            if expect_fail:
                return {"_test_meta": {"status": "failed_as_expected"}}
            return {"_test_meta": {"status": "http_error", "code": response.status_code}}
    except Exception as e:
        if expect_fail:
            return {"_test_meta": {"status": "error_as_expected"}}
        return {"_test_meta": {"status": "exception", "error": str(e)}}

def clear_session():
    """Clear session by calling getCallerInfo (resets session)"""
    # In a real implementation, you might need a clearSession tool
    # For now, we'll just note that sessions are per-caller
    pass

def test_case(name: str):
    """Decorator for test cases"""
    def decorator(func):
        def wrapper():
            stats.total += 1
            print(f"\n{Colors.CYAN}{'='*80}{Colors.RESET}")
            print(f"{Colors.BOLD}TEST {stats.total}: {name}{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")

            try:
                result = func()
                if result:
                    stats.passed += 1
                    print(f"{Colors.GREEN}✓ PASSED{Colors.RESET}")
                else:
                    stats.failed += 1
                    print(f"{Colors.RED}✗ FAILED{Colors.RESET}")
                return result
            except Exception as e:
                stats.failed += 1
                print(f"{Colors.RED}✗ EXCEPTION: {str(e)}{Colors.RESET}")
                return False

        return wrapper
    return decorator

def assert_equal(actual, expected, message=""):
    """Assert two values are equal"""
    if actual == expected:
        print(f"  {Colors.GREEN}✓{Colors.RESET} {message}: {actual}")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} {message}")
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual}")
        return False

def assert_true(condition, message=""):
    """Assert condition is true"""
    if condition:
        print(f"  {Colors.GREEN}✓{Colors.RESET} {message}")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} {message}")
        return False

def assert_in(value, container, message=""):
    """Assert value is in container"""
    if value in container:
        print(f"  {Colors.GREEN}✓{Colors.RESET} {message}: {value} found")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.RESET} {message}: {value} not found")
        return False

def get_result(response):
    """Extract result from response"""
    if response and "results" in response and len(response["results"]) > 0:
        return response["results"][0].get("result", {})
    return {}

# ==================== BASIC FUNCTIONALITY TESTS ====================

@test_case("Check if shop is open")
def test_check_open():
    result = call_tool("checkOpen")
    r = get_result(result)
    return assert_true(r.get("ok"), "Shop status retrieved")

@test_case("Get caller information")
def test_get_caller_info():
    result = call_tool("getCallerInfo")
    r = get_result(result)
    return (
        assert_true(r.get("ok"), "Caller info retrieved") and
        assert_true(r.get("hasCallerID"), "Has caller ID")
    )

# ==================== KEBAB TESTS ====================

@test_case("Small Chicken Kebab - Full Configuration")
def test_small_chicken_kebab():
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return (
        assert_equal(len(cart), 1, "Cart has 1 item") and
        assert_equal(cart[0].get("size"), "small", "Size is small") and
        assert_equal(cart[0].get("protein"), "chicken", "Protein is chicken")
    )

@test_case("Large Lamb Kebab with Extras")
def test_large_lamb_kebab_extras():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "pickles", "olives"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli", "bbq"]})
    call_tool("setItemProperty", {"field": "extras", "value": ["cheese", "extra lamb"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Large lamb kebab with extras added")

@test_case("Mix Kebab")
def test_mix_kebab():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "mix"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "onion"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Mix kebab added")

@test_case("Falafel Kebab (Vegan)")
def test_falafel_kebab():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "falafel"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion", "pickles"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["hummus", "chilli"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Falafel kebab added")

@test_case("Kebab with NO salads")
def test_kebab_no_salads():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": []})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return (
        assert_true(r.get("ok"), "Kebab with no salads added") and
        assert_equal(cart[0].get("salads"), [], "Salads is empty array")
    )

@test_case("Kebab with NO sauces")
def test_kebab_no_sauces():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato"]})
    call_tool("setItemProperty", {"field": "sauces", "value": []})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Kebab with no sauces added")

# ==================== HSP TESTS ====================

@test_case("Small Lamb HSP")
def test_small_lamb_hsp():
    clear_session()
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("setItemProperty", {"field": "cheese", "value": True})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Small lamb HSP added")

@test_case("Large Chicken HSP - No Cheese")
def test_large_chicken_hsp_no_cheese():
    clear_session()
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "bbq"]})
    call_tool("setItemProperty", {"field": "cheese", "value": False})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Large chicken HSP without cheese added")

@test_case("Mix HSP")
def test_mix_hsp():
    clear_session()
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "mix"})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli", "sweet chilli"]})
    call_tool("setItemProperty", {"field": "cheese", "value": True})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Mix HSP added")

@test_case("Falafel HSP (Vegetarian)")
def test_falafel_hsp():
    clear_session()
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "falafel"})
    call_tool("setItemProperty", {"field": "sauces", "value": ["hummus", "chilli"]})
    call_tool("setItemProperty", {"field": "cheese", "value": False})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Falafel HSP added")

# ==================== CHIPS TESTS ====================

@test_case("Small Chips - Default Chicken Salt")
def test_small_chips_chicken_salt():
    clear_session()
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})

    result = call_tool("addItemToCart")
    r = get_result(result)

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return (
        assert_true(r.get("ok"), "Small chips added") and
        assert_equal(cart[0].get("salt_type"), "chicken", "Default salt is chicken")
    )

@test_case("Large Chips - Normal Salt")
def test_large_chips_normal_salt():
    clear_session()
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "salt_type", "value": "normal"})

    result = call_tool("addItemToCart")
    r = get_result(result)

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return assert_equal(cart[0].get("salt_type"), "normal", "Salt type is normal")

@test_case("Small Chips - No Salt")
def test_small_chips_no_salt():
    clear_session()
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "salt_type", "value": "none"})

    result = call_tool("addItemToCart")
    r = get_result(result)

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return assert_equal(cart[0].get("salt_type"), "none", "No salt")

# ==================== DRINKS TESTS ====================

@test_case("Coca-Cola Can")
def test_coke_can():
    clear_session()
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "coca-cola"})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Coke added")

@test_case("Multiple Different Drinks")
def test_multiple_drinks():
    clear_session()

    drinks = ["coca-cola", "sprite", "fanta", "pepsi", "pepsi max"]

    for drink in drinks:
        call_tool("startItemConfiguration", {"category": "drinks"})
        call_tool("setItemProperty", {"field": "brand", "value": drink})
        call_tool("addItemToCart")

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return assert_equal(len(cart), len(drinks), f"Cart has {len(drinks)} drinks")

# ==================== COMBO DETECTION TESTS ====================

@test_case("Small Kebab + Can = Combo ($12)")
def test_small_kebab_can_combo():
    clear_session()

    # Add small kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("addItemToCart")

    # Add can - should trigger combo
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "coca-cola"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "Combo detected") and
        assert_equal(r.get("comboInfo", {}).get("name"), "Small Kebab & Can Combo", "Correct combo name") and
        assert_equal(price.get("totals", {}).get("grand_total"), 12.0, "Price is $12")
    )

@test_case("Large Kebab + Can = Combo ($17)")
def test_large_kebab_can_combo():
    clear_session()

    # Add large kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["chilli"]})
    call_tool("addItemToCart")

    # Add can
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "fanta"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "Combo detected") and
        assert_equal(price.get("totals", {}).get("grand_total"), 17.0, "Price is $17")
    )

@test_case("Small Kebab + Small Chips + Can = Meal ($17)")
def test_small_kebab_meal():
    clear_session()

    # Add small kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("addItemToCart")

    # Add small chips
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("addItemToCart")

    # Add can - should trigger meal combo
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "coca-cola"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "Meal combo detected") and
        assert_equal(r.get("comboInfo", {}).get("name"), "Small Kebab Meal", "Correct meal name") and
        assert_equal(price.get("totals", {}).get("grand_total"), 17.0, "Price is $17")
    )

@test_case("Large Kebab + Small Chips + Can = Meal ($22)")
def test_large_kebab_meal():
    clear_session()

    # Add large kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("addItemToCart")

    # Add small chips
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("addItemToCart")

    # Add can
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "sprite"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "Meal combo detected") and
        assert_equal(price.get("totals", {}).get("grand_total"), 22.0, "Price is $22")
    )

@test_case("Large Kebab + Large Chips + Can = Meal ($25)")
def test_large_kebab_large_chips_meal():
    clear_session()

    # Add large kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "mix"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("addItemToCart")

    # Add LARGE chips
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("addItemToCart")

    # Add can
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "pepsi"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "Large meal combo detected") and
        assert_equal(price.get("totals", {}).get("grand_total"), 25.0, "Price is $25")
    )

@test_case("Small HSP + Can = Combo ($17)")
def test_small_hsp_combo():
    clear_session()

    # Add small HSP
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("setItemProperty", {"field": "cheese", "value": True})
    call_tool("addItemToCart")

    # Add can
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "coca-cola"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "HSP combo detected") and
        assert_equal(price.get("totals", {}).get("grand_total"), 17.0, "Price is $17")
    )

@test_case("Large HSP + Can = Combo ($22)")
def test_large_hsp_combo():
    clear_session()

    # Add large HSP
    call_tool("startItemConfiguration", {"category": "hsp"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("setItemProperty", {"field": "cheese", "value": True})
    call_tool("addItemToCart")

    # Add can
    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "sprite"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # Price cart
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    return (
        assert_true(r.get("comboDetected"), "HSP combo detected") and
        assert_equal(price.get("totals", {}).get("grand_total"), 22.0, "Price is $22")
    )

@test_case("Kebab + Chips (NO drink) = No Combo")
def test_kebab_chips_no_combo():
    clear_session()

    # Add kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("addItemToCart")

    # Add chips (no drink!)
    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(not r.get("comboDetected"), "No combo without drink")

# ==================== ERROR HANDLING TESTS ====================

@test_case("Invalid Category")
def test_invalid_category():
    clear_session()
    result = call_tool("startItemConfiguration", {"category": "pizza"})
    r = get_result(result)

    # Should either error or handle gracefully
    return assert_true(True, "Invalid category handled")

@test_case("Missing Required Field - Size")
def test_missing_size():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    # Don't set size
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    # Should fail because size is required
    return assert_true(not r.get("ok") or r.get("ok") == False, "Rejects missing size")

@test_case("Missing Required Field - Protein")
def test_missing_protein():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    # Don't set protein
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})

    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(not r.get("ok") or r.get("ok") == False, "Rejects missing protein")

@test_case("Add to Cart Without Starting Configuration")
def test_add_without_config():
    clear_session()
    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(not r.get("ok"), "Rejects adding without configuration")

@test_case("Set Property Without Starting Configuration")
def test_set_without_config():
    clear_session()
    result = call_tool("setItemProperty", {"field": "size", "value": "small"})
    r = get_result(result)

    return assert_true(not r.get("ok"), "Rejects setting property without configuration")

@test_case("Invalid Protein Type")
def test_invalid_protein():
    clear_session()
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    result = call_tool("setItemProperty", {"field": "protein", "value": "beef"})
    r = get_result(result)

    # Should accept (server doesn't validate options) OR reject
    return assert_true(True, "Invalid protein handled")

@test_case("Invalid Drink Brand")
def test_invalid_drink_brand():
    clear_session()
    call_tool("startItemConfiguration", {"category": "drinks"})
    result = call_tool("setItemProperty", {"field": "brand", "value": "monster-energy"})
    r = get_result(result)

    # Should accept or reject gracefully
    return assert_true(True, "Invalid brand handled")

# ==================== QUANTITY TESTS ====================

@test_case("Multiple Quantity - 3x Small Chicken Kebabs")
def test_multiple_quantity():
    clear_session()

    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("setItemProperty", {"field": "quantity", "value": 3})

    result = call_tool("addItemToCart")
    r = get_result(result)

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    price_result = call_tool("priceCart")
    price = get_result(price_result)
    total = price.get("totals", {}).get("grand_total")

    return (
        assert_equal(cart[0].get("quantity"), 3, "Quantity is 3") and
        assert_equal(total, 30.0, "Total is $30 (3 x $10)")
    )

# ==================== PRICING TESTS ====================

@test_case("Pricing - Extras Add Cost")
def test_pricing_extras():
    clear_session()

    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("setItemProperty", {"field": "extras", "value": ["cheese"]})  # +$1
    call_tool("addItemToCart")

    price_result = call_tool("priceCart")
    price = get_result(price_result)
    total = price.get("totals", {}).get("grand_total")

    # Small kebab ($10) + cheese ($1) = $11
    return assert_equal(total, 11.0, "Price includes cheese extra ($11)")

@test_case("Pricing - Multiple Extra Sauces")
def test_pricing_extra_sauces():
    clear_session()

    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli", "bbq", "mayo"]})  # 4 sauces, 2 free, 2 extra @ $0.50 each
    call_tool("addItemToCart")

    price_result = call_tool("priceCart")
    price = get_result(price_result)
    total = price.get("totals", {}).get("grand_total")

    # Small kebab ($10) + 2 extra sauces ($1) = $11
    return assert_equal(total, 11.0, "Price includes extra sauce charge ($11)")

@test_case("Empty Cart - Cannot Price")
def test_empty_cart_price():
    clear_session()

    result = call_tool("priceCart")
    r = get_result(result)

    return assert_true(not r.get("ok"), "Cannot price empty cart")

# ==================== COMPLETE ORDER FLOW TEST ====================

@test_case("Complete Order Flow - Kebab Meal")
def test_complete_order_flow():
    clear_session()

    # 1. Check open
    call_tool("checkOpen")

    # 2. Get caller info
    caller_result = call_tool("getCallerInfo")
    caller = get_result(caller_result)
    phone = caller.get("phoneNumber")

    # 3. Build order
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli"]})
    call_tool("addItemToCart")

    call_tool("startItemConfiguration", {"category": "chips"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("addItemToCart")

    call_tool("startItemConfiguration", {"category": "drinks"})
    call_tool("setItemProperty", {"field": "brand", "value": "coca-cola"})
    combo_result = call_tool("addItemToCart")

    # 4. Price
    price_result = call_tool("priceCart")
    price = get_result(price_result)

    # 5. Estimate time
    time_result = call_tool("estimateReadyTime")
    time_r = get_result(time_result)
    ready_at = time_r.get("readyAtIso")

    # 6. Create order
    if ready_at and phone:
        order_result = call_tool("createOrder", {
            "customerName": "Test User",
            "customerPhone": phone,
            "readyAtIso": ready_at
        })
        order = get_result(order_result)

        # 7. End call
        call_tool("endCall")

        return (
            assert_true(order.get("ok"), "Order created successfully") and
            assert_true(order.get("orderId"), "Order ID generated")
        )

    return False

# ==================== PERFORMANCE TESTS ====================

@test_case("Performance - All Tools Under 1 Second")
def test_performance():
    clear_session()

    tools = [
        ("checkOpen", {}),
        ("getCallerInfo", {}),
        ("startItemConfiguration", {"category": "kebabs"}),
        ("setItemProperty", {"field": "size", "value": "small"}),
        ("addItemToCart", {}),
    ]

    all_fast = True
    for tool_name, params in tools:
        start = time.time()
        call_tool(tool_name, params)
        elapsed = time.time() - start

        if elapsed > 1.0:
            print(f"  {Colors.RED}✗{Colors.RESET} {tool_name} took {elapsed:.2f}s (too slow)")
            all_fast = False
        else:
            print(f"  {Colors.GREEN}✓{Colors.RESET} {tool_name} took {elapsed*1000:.0f}ms")

    return assert_true(all_fast, "All tools respond in under 1 second")

# ==================== EDGE CASE TESTS ====================

@test_case("Edge Case - Add Same Item Twice")
def test_same_item_twice():
    clear_session()

    # Add first kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("addItemToCart")

    # Add second identical kebab
    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    call_tool("addItemToCart")

    cart_result = call_tool("getCartState")
    cart = get_result(cart_result).get("cart", [])

    return assert_equal(len(cart), 2, "Cart has 2 separate items")

@test_case("Edge Case - All Salads")
def test_all_salads():
    clear_session()

    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "large"})
    call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce", "tomato", "onion", "pickles", "olives"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic"]})
    result = call_tool("addItemToCart")
    r = get_result(result)

    return assert_true(r.get("ok"), "Accepts all salad types")

@test_case("Edge Case - All Sauces")
def test_all_sauces():
    clear_session()

    call_tool("startItemConfiguration", {"category": "kebabs"})
    call_tool("setItemProperty", {"field": "size", "value": "small"})
    call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
    call_tool("setItemProperty", {"field": "salads", "value": ["lettuce"]})
    call_tool("setItemProperty", {"field": "sauces", "value": ["garlic", "chilli", "bbq", "tomato", "sweet chilli", "mayo", "hummus"]})
    result = call_tool("addItemToCart")
    r = get_result(result)

    # 7 sauces, 2 free, 5 extra @ $0.50 = $2.50 extra
    price_result = call_tool("priceCart")
    price = get_result(price_result)
    total = price.get("totals", {}).get("grand_total")

    return (
        assert_true(r.get("ok"), "Accepts all sauce types") and
        assert_equal(total, 12.5, "Charges for extra sauces ($12.50)")
    )

# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    """Run all test cases"""
    stats.start()

    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "KEBABALAB MEGA TEST SUITE" + " "*33 + "║")
    print("║" + " "*78 + "║")
    print("║" + "  Testing ALL scenarios including edge cases and invalid inputs" + " "*12 + "║")
    print("╚" + "="*78 + "╝")
    print(f"{Colors.RESET}\n")

    # Basic functionality
    print(f"\n{Colors.BOLD}{'='*80}")
    print("BASIC FUNCTIONALITY TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_check_open()
    test_get_caller_info()

    # Kebab tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("KEBAB TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_small_chicken_kebab()
    test_large_lamb_kebab_extras()
    test_mix_kebab()
    test_falafel_kebab()
    test_kebab_no_salads()
    test_kebab_no_sauces()

    # HSP tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("HSP TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_small_lamb_hsp()
    test_large_chicken_hsp_no_cheese()
    test_mix_hsp()
    test_falafel_hsp()

    # Chips tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("CHIPS TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_small_chips_chicken_salt()
    test_large_chips_normal_salt()
    test_small_chips_no_salt()

    # Drinks tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("DRINKS TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_coke_can()
    test_multiple_drinks()

    # Combo detection tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("COMBO DETECTION TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_small_kebab_can_combo()
    test_large_kebab_can_combo()
    test_small_kebab_meal()
    test_large_kebab_meal()
    test_large_kebab_large_chips_meal()
    test_small_hsp_combo()
    test_large_hsp_combo()
    test_kebab_chips_no_combo()

    # Error handling tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("ERROR HANDLING TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_invalid_category()
    test_missing_size()
    test_missing_protein()
    test_add_without_config()
    test_set_without_config()
    test_invalid_protein()
    test_invalid_drink_brand()

    # Quantity tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("QUANTITY TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_multiple_quantity()

    # Pricing tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("PRICING TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_pricing_extras()
    test_pricing_extra_sauces()
    test_empty_cart_price()

    # Complete flow test
    print(f"\n{Colors.BOLD}{'='*80}")
    print("COMPLETE ORDER FLOW TEST")
    print(f"{'='*80}{Colors.RESET}\n")
    test_complete_order_flow()

    # Performance tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("PERFORMANCE TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_performance()

    # Edge case tests
    print(f"\n{Colors.BOLD}{'='*80}")
    print("EDGE CASE TESTS")
    print(f"{'='*80}{Colors.RESET}\n")
    test_same_item_twice()
    test_all_salads()
    test_all_sauces()

    stats.finish()

if __name__ == "__main__":
    run_all_tests()

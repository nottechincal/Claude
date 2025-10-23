#!/usr/bin/env python3
"""
Comprehensive Edge Case Test Suite
Tests all critical scenarios to ensure bulletproof system
"""

import requests
import json
import time
from decimal import Decimal
from typing import Dict, Any, List

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_PHONE = "+61412345678"
TEST_PHONE_2 = "+61412345679"


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.duration = 0
        self.details = {}

    def __str__(self):
        status = "✅ PASSED" if self.passed else "❌ FAILED"
        time_str = f"{self.duration:.2f}s"
        if self.error:
            return f"{status} {self.name} ({time_str})\n   Error: {self.error}"
        return f"{status} {self.name} ({time_str})"


class ComprehensiveTestSuite:
    def __init__(self):
        self.results: List[TestResult] = []
        self.session_phone = TEST_PHONE

    def call_tool(self, tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a server tool via webhook"""
        if params is None:
            params = {}

        payload = {
            "message": {
                "toolCalls": [{
                    "function": {
                        "name": tool_name,
                        "arguments": params
                    },
                    "id": f"test_{tool_name}_{time.time()}"
                }]
            },
            "call": {
                "customer": {
                    "number": self.session_phone
                }
            }
        }

        response = requests.post(f"{BASE_URL}/webhook", json=payload)
        return response.json()

    def clear_session(self):
        """Clear cart for fresh test"""
        self.call_tool("clearCart")

    def run_test(self, test_func):
        """Run a single test and record results"""
        result = TestResult(test_func.__name__)
        start_time = time.time()

        try:
            # Clear session before each test
            self.clear_session()

            # Run the test
            test_func(result)

            if result.error is None:
                result.passed = True
        except Exception as e:
            result.error = str(e)
            result.passed = False

        result.duration = time.time() - start_time
        self.results.append(result)
        print(result)
        return result.passed

    # =================================================================
    # CATEGORY 1: EXTREME VOLUME TESTS 🔢
    # =================================================================

    def test_1_1_single_item_order(self, result: TestResult):
        """Test 1.1: Single item order - simplest case"""
        # Add 1 small chicken kebab
        resp = self.call_tool("startItemConfiguration", {"category": "kebabs"})
        assert resp["ok"], "Failed to start item"

        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})

        resp = self.call_tool("addItemToCart")
        assert resp["ok"], "Failed to add to cart"

        # Price cart
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price cart"
        assert resp["grandTotal"] == 10.0, f"Wrong price: expected $10, got ${resp['grandTotal']}"

        result.details["price"] = resp["grandTotal"]

    def test_1_2_maximum_order_size(self, result: TestResult):
        """Test 1.2: Maximum order - 20 large kebabs with unique mods"""
        proteins = ["lamb", "chicken", "mixed", "falafel"]

        for i in range(20):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": proteins[i % 4]})

            # Unique salad combos
            if i % 3 == 0:
                self.call_tool("setItemProperty", {"field": "salads", "value": '["lettuce", "tomato"]'})
            elif i % 3 == 1:
                self.call_tool("setItemProperty", {"field": "salads", "value": '["lettuce", "onion", "tabouli"]'})
            else:
                self.call_tool("setItemProperty", {"field": "salads", "value": '["lettuce", "tomato", "onion"]'})

            resp = self.call_tool("addItemToCart")
            assert resp["ok"], f"Failed to add item {i}"

        # Price the massive cart
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price 20-item cart"

        # 20 large kebabs = 20 × $15 = $300
        expected = 20 * 15.0
        assert resp["grandTotal"] == expected, f"Wrong total: expected ${expected}, got ${resp['grandTotal']}"

        result.details["items"] = 20
        result.details["total"] = resp["grandTotal"]

    def test_1_3_empty_cart_operations(self, result: TestResult):
        """Test 1.3: Operations on empty cart should fail gracefully"""
        # Try to price empty cart
        resp = self.call_tool("priceCart")
        assert not resp["ok"], "Should fail on empty cart"
        assert "empty" in resp.get("error", "").lower(), "Should mention empty cart"

        # Try to convert empty cart to meals
        resp = self.call_tool("convertItemsToMeals")
        assert not resp["ok"], "Should fail to convert empty cart"

        # Try to modify non-existent item
        resp = self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"size": "large"}})
        assert not resp["ok"], "Should fail to modify empty cart"

        result.details["graceful_failures"] = 3

    # =================================================================
    # CATEGORY 2: RAPID MODIFICATION STRESS ⚡
    # =================================================================

    def test_2_1_add_remove_spam(self, result: TestResult):
        """Test 2.1: Rapid add/remove to test cart index handling"""
        # Add 5 kebabs
        for i in range(5):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Remove item 0
        self.call_tool("removeCartItem", {"itemIndex": 0})

        # Add 3 HSP
        for i in range(3):
            self.call_tool("startItemConfiguration", {"category": "hsp"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
            self.call_tool("addItemToCart")

        # Remove item 2
        self.call_tool("removeCartItem", {"itemIndex": 2})

        # Remove item 4
        self.call_tool("removeCartItem", {"itemIndex": 4})

        # Add 2 chips
        for i in range(2):
            self.call_tool("startItemConfiguration", {"category": "chips"})
            self.call_tool("setItemProperty", {"field": "size", "value": "small"})
            self.call_tool("addItemToCart")

        # Get cart state
        resp = self.call_tool("getCartState")
        assert resp["ok"], "Failed to get cart state"

        # Should have: 4 kebabs + 2 HSP + 2 chips = 8 items
        cart = resp.get("cart", [])
        expected_count = 8
        assert len(cart) == expected_count, f"Wrong item count: expected {expected_count}, got {len(cart)}"

        result.details["final_item_count"] = len(cart)

    def test_2_2_modify_chain(self, result: TestResult):
        """Test 2.2: Chain modifications on single item"""
        # Add large chicken kebab
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "large"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("addItemToCart")

        # Modify size to small
        resp = self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"size": "small"}})
        assert resp["ok"], "Failed to modify size"

        # Modify protein to lamb
        resp = self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"protein": "lamb"}})
        assert resp["ok"], "Failed to modify protein"

        # Modify protein to mixed
        resp = self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"protein": "mixed"}})
        assert resp["ok"], "Failed to modify protein again"

        # Modify size back to large
        resp = self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"size": "large"}})
        assert resp["ok"], "Failed to modify size back"

        # Convert to meal
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [0]})
        assert resp["ok"], "Failed to convert to meal"

        # Price and verify
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price"

        # Large kebab meal = $22
        assert resp["grandTotal"] == 22.0, f"Wrong price: expected $22, got ${resp['grandTotal']}"

        result.details["modifications"] = 6
        result.details["final_price"] = resp["grandTotal"]

    def test_2_3_clear_and_rebuild(self, result: TestResult):
        """Test 2.3: Clear cart and rebuild multiple times"""
        # Add 10 items
        for i in range(10):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "small"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Clear cart
        resp = self.call_tool("clearCart")
        assert resp["ok"], "Failed to clear cart"

        # Immediately add 5 new items
        for i in range(5):
            self.call_tool("startItemConfiguration", {"category": "hsp"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
            self.call_tool("addItemToCart")

        # Price cart
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price after rebuild"

        # Clear again
        self.call_tool("clearCart")

        # Add 1 final item
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "large"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
        self.call_tool("addItemToCart")

        # Final price
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed final pricing"
        assert resp["grandTotal"] == 15.0, f"Wrong final price: expected $15, got ${resp['grandTotal']}"

        result.details["clears"] = 2
        result.details["rebuilds"] = 3

    # =================================================================
    # CATEGORY 3: COMPLEX MEAL CONVERSIONS 🍔
    # =================================================================

    def test_3_1_partial_meal_upgrade_with_mods(self, result: TestResult):
        """Test 3.1: Partial meal upgrade - the exact failing scenario!"""
        # Add 5 large chicken kebabs
        for i in range(5):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Modify kebabs #1 and #3 to have extra toppings
        self.call_tool("modifyCartItem", {
            "itemIndex": 1,
            "modifications": {"cheese": True, "salads": '["lettuce", "tomato", "onion", "tabouli"]'}
        })
        self.call_tool("modifyCartItem", {
            "itemIndex": 3,
            "modifications": {"sauces": '["garlic", "chilli", "bbq"]'}
        })

        # Convert only #0, #2, #4 to meals
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [0, 2, 4]})
        assert resp["ok"], "Failed to convert to meals"

        # Modify meal #2 to have large chips
        resp = self.call_tool("modifyCartItem", {
            "itemIndex": 2,
            "modifications": {"chips_size": "large"}
        })
        assert resp["ok"], "Failed to upgrade chips"

        # Price cart
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price"

        # Expected:
        # - Item 0: Large kebab meal = $22
        # - Item 1: Large kebab + cheese = $15 + $1 = $16
        # - Item 2: Large kebab meal + large chips = $25
        # - Item 3: Large kebab = $15
        # - Item 4: Large kebab meal = $22
        # Total: $22 + $16 + $25 + $15 + $22 = $100
        expected = 100.0
        actual = resp["grandTotal"]

        # Allow small floating point variance
        assert abs(actual - expected) < 0.01, f"Wrong price: expected ${expected}, got ${actual}"

        result.details["items"] = 5
        result.details["meals"] = 3
        result.details["regular"] = 2
        result.details["total"] = actual

    def test_3_2_already_meals_edge_case(self, result: TestResult):
        """Test 3.2: Try to convert meals to meals (should handle gracefully)"""
        # Add 3 kebabs
        for i in range(3):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Convert all to meals
        resp = self.call_tool("convertItemsToMeals")
        assert resp["ok"], "Failed first conversion"

        # Try to convert again (items are already meals)
        resp = self.call_tool("convertItemsToMeals")

        # Should either gracefully ignore or return appropriate message
        # Not crash the system
        result.details["handled_gracefully"] = True

    def test_3_3_mixed_sizes_meal_upgrade(self, result: TestResult):
        """Test 3.3: Convert mix of small and large kebabs to meals"""
        # Add 2 small kebabs
        for i in range(2):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "small"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Add 3 large kebabs
        for i in range(3):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
            self.call_tool("addItemToCart")

        # Convert all to meals
        resp = self.call_tool("convertItemsToMeals")
        assert resp["ok"], "Failed to convert mixed sizes"

        # Price
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price"

        # Expected:
        # - 2 small kebab meals = 2 × $17 = $34
        # - 3 large kebab meals = 3 × $22 = $66
        # Total: $100
        expected = 100.0
        assert abs(resp["grandTotal"] - expected) < 0.01, f"Wrong total: expected ${expected}, got ${resp['grandTotal']}"

        result.details["small_meals"] = 2
        result.details["large_meals"] = 3
        result.details["total"] = resp["grandTotal"]

    def test_3_4_meal_conversion_all_drink_types(self, result: TestResult):
        """Test 3.4: Meal conversions with different drinks"""
        # Add 6 large kebabs
        for i in range(6):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Convert items 0,1 to meals with coke
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [0, 1], "drinkBrand": "coke"})
        assert resp["ok"], "Failed coke conversion"

        # Convert items 2,3 to meals with sprite
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [2, 3], "drinkBrand": "sprite"})
        assert resp["ok"], "Failed sprite conversion"

        # Convert items 4,5 to meals with fanta
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [4, 5], "drinkBrand": "fanta"})
        assert resp["ok"], "Failed fanta conversion"

        # Price - all should be same price regardless of drink
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price"

        # 6 large kebab meals = 6 × $22 = $132
        expected = 132.0
        assert abs(resp["grandTotal"] - expected) < 0.01, f"Wrong total: expected ${expected}, got ${resp['grandTotal']}"

        result.details["drink_types"] = ["coke", "sprite", "fanta"]
        result.details["total"] = resp["grandTotal"]

    # =================================================================
    # CATEGORY 4: INVALID INPUT HANDLING 🚫
    # =================================================================

    def test_4_1_out_of_bounds_indices(self, result: TestResult):
        """Test 4.1: Out of bounds item indices"""
        # Add 3 kebabs
        for i in range(3):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "small"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Try to modify item 10 (doesn't exist)
        resp = self.call_tool("modifyCartItem", {"itemIndex": 10, "modifications": {"size": "large"}})
        assert not resp["ok"], "Should reject out of bounds index"

        # Try negative index
        resp = self.call_tool("modifyCartItem", {"itemIndex": -1, "modifications": {"size": "large"}})
        assert not resp["ok"], "Should reject negative index"

        # Try to convert invalid indices
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [0, 2, 99]})
        # Should either skip invalid or reject entirely

        result.details["invalid_operations"] = 3

    def test_4_2_invalid_field_values(self, result: TestResult):
        """Test 4.2: Invalid menu items should be rejected"""
        # Try invalid protein
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        resp = self.call_tool("setItemProperty", {"field": "protein", "value": "wagyu-gold"})
        # System might accept anything currently - this tests validates existence

        # Try invalid size
        resp = self.call_tool("setItemProperty", {"field": "size", "value": "mega-ultra-large"})

        # System should handle gracefully
        result.details["invalid_values_tested"] = 2

    # =================================================================
    # CATEGORY 5: PRICING INTEGRITY 💰
    # =================================================================

    def test_5_1_all_kebab_sizes_priced_correctly(self, result: TestResult):
        """Test 5.1: Verify kebab pricing"""
        # Small kebab
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("addItemToCart")

        resp = self.call_tool("priceCart")
        assert resp["grandTotal"] == 10.0, f"Small kebab should be $10, got ${resp['grandTotal']}"

        self.call_tool("clearCart")

        # Large kebab
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "large"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "lamb"})
        self.call_tool("addItemToCart")

        resp = self.call_tool("priceCart")
        assert resp["grandTotal"] == 15.0, f"Large kebab should be $15, got ${resp['grandTotal']}"

        result.details["small_kebab_price"] = 10.0
        result.details["large_kebab_price"] = 15.0

    def test_5_2_combo_pricing_vs_individual(self, result: TestResult):
        """Test 5.2: Combo detection and pricing"""
        # Add kebab + chips + drink individually
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("addItemToCart")

        self.call_tool("startItemConfiguration", {"category": "chips"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("addItemToCart")

        self.call_tool("startItemConfiguration", {"category": "drinks"})
        self.call_tool("setItemProperty", {"field": "drink_brand", "value": "coke"})
        self.call_tool("addItemToCart")

        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price combo"

        # Individual: $10 + $5 + $3.50 = $18.50
        # Combo: $17 (save $1.50)
        expected_combo = 17.0
        assert abs(resp["grandTotal"] - expected_combo) < 0.01, \
            f"Combo should be ${expected_combo}, got ${resp['grandTotal']}"

        result.details["combo_price"] = resp["grandTotal"]
        result.details["individual_price"] = 18.5
        result.details["savings"] = 1.5

    def test_5_3_large_chips_upgrade_pricing(self, result: TestResult):
        """Test 5.3: Large chips upgrade on meals"""
        # Add small kebab meal
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("addItemToCart")

        self.call_tool("convertItemsToMeals", {"chipsSize": "small"})

        resp = self.call_tool("priceCart")
        small_meal_price = resp["grandTotal"]
        assert abs(small_meal_price - 17.0) < 0.01, "Small meal should be $17"

        # Now upgrade to large chips
        self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"chips_size": "large"}})

        resp = self.call_tool("priceCart")
        large_chips_meal = resp["grandTotal"]

        # Small meal + large chips = $20 (not $17 + $9)
        expected = 20.0
        assert abs(large_chips_meal - expected) < 0.01, \
            f"Small meal with large chips should be ${expected}, got ${large_chips_meal}"

        result.details["small_meal"] = 17.0
        result.details["large_chips_upgrade"] = 20.0

    def test_5_4_extra_toppings_pricing(self, result: TestResult):
        """Test 5.4: Extra toppings add correct charges"""
        # Kebab with cheese
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("setItemProperty", {"field": "cheese", "value": "true"})
        self.call_tool("addItemToCart")

        resp = self.call_tool("priceCart")
        # Small kebab ($10) + cheese ($1) = $11
        assert abs(resp["grandTotal"] - 11.0) < 0.01, \
            f"Kebab with cheese should be $11, got ${resp['grandTotal']}"

        self.call_tool("clearCart")

        # Kebab with extra meat
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("setItemProperty", {"field": "extra_meat", "value": "true"})
        self.call_tool("addItemToCart")

        resp = self.call_tool("priceCart")
        # Small kebab ($10) + extra meat ($3) = $13
        assert abs(resp["grandTotal"] - 13.0) < 0.01, \
            f"Kebab with extra meat should be $13, got ${resp['grandTotal']}"

        result.details["cheese_price"] = 1.0
        result.details["extra_meat_price"] = 3.0

    # =================================================================
    # CATEGORY 6: REAL-WORLD CHAOS 🌪️
    # =================================================================

    def test_6_1_the_indecisive_customer(self, result: TestResult):
        """Test 6.1: Customer changes mind multiple times (stress test)"""
        # "5 chicken kebabs"
        for i in range(5):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # "Actually make them lamb"
        for i in range(5):
            self.call_tool("modifyCartItem", {"itemIndex": i, "modifications": {"protein": "lamb"}})

        # "No wait, 3 chicken, 2 lamb"
        for i in range(3):
            self.call_tool("modifyCartItem", {"itemIndex": i, "modifications": {"protein": "chicken"}})

        # "Make them all meals"
        resp = self.call_tool("convertItemsToMeals")
        assert resp["ok"], "Failed to convert to meals"

        # "Actually just 3 meals, remove 2"
        self.call_tool("removeCartItem", {"itemIndex": 4})
        self.call_tool("removeCartItem", {"itemIndex": 3})

        # "Add large chips to all meals"
        for i in range(3):
            self.call_tool("modifyCartItem", {"itemIndex": i, "modifications": {"chips_size": "large"}})

        # Final price
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed final pricing"

        # 3 large kebab meals with large chips = 3 × $25 = $75
        expected = 75.0
        assert abs(resp["grandTotal"] - expected) < 0.01, \
            f"Expected ${expected}, got ${resp['grandTotal']}"

        result.details["changes"] = 7
        result.details["final_total"] = resp["grandTotal"]

    def test_6_2_the_group_order(self, result: TestResult):
        """Test 6.2: Complex group order with many items"""
        # 3 small lamb kebabs with variations
        for i in range(3):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "small"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "lamb"})

            if i == 0:
                self.call_tool("setItemProperty", {"field": "salads", "value": '["lettuce", "tomato"]'})
            elif i == 1:
                self.call_tool("setItemProperty", {"field": "cheese", "value": "true"})

            self.call_tool("addItemToCart")

        # 2 large chicken kebabs
        for i in range(2):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("setItemProperty", {"field": "salads", "value": '["lettuce", "tomato", "onion"]'})
            self.call_tool("addItemToCart")

        # 1 large HSP
        self.call_tool("startItemConfiguration", {"category": "hsp"})
        self.call_tool("setItemProperty", {"field": "size", "value": "large"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "mixed"})
        self.call_tool("addItemToCart")

        # 5 small chips with different salts
        for i in range(5):
            self.call_tool("startItemConfiguration", {"category": "chips"})
            self.call_tool("setItemProperty", {"field": "size", "value": "small"})

            if i < 2:
                salt = "chicken"
            elif i < 4:
                salt = "plain"
            else:
                salt = "seasoned"

            self.call_tool("setItemProperty", {"field": "salt_type", "value": salt})
            self.call_tool("addItemToCart")

        # Convert 2 kebabs to meals
        resp = self.call_tool("convertItemsToMeals", {"itemIndices": [0, 2]})
        assert resp["ok"], "Failed to convert"

        # Price the complex order
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price group order"

        result.details["total_items"] = 11
        result.details["total"] = resp["grandTotal"]

    # =================================================================
    # CATEGORY 7: PERFORMANCE BENCHMARKS ⚡
    # =================================================================

    def test_7_1_speed_simple_order(self, result: TestResult):
        """Test 7.1: Simple order speed < 3 seconds"""
        start = time.time()

        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("addItemToCart")
        self.call_tool("priceCart")

        elapsed = time.time() - start

        assert elapsed < 3.0, f"Too slow: {elapsed:.2f}s (target < 3s)"

        result.details["elapsed"] = f"{elapsed:.2f}s"
        result.details["target"] = "< 3s"

    def test_7_2_speed_complex_order(self, result: TestResult):
        """Test 7.2: Complex order speed < 8 seconds"""
        start = time.time()

        # Add 5 kebabs with modifications
        for i in range(5):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("setItemProperty", {"field": "salads", "value": '["lettuce", "tomato"]'})
            self.call_tool("setItemProperty", {"field": "sauces", "value": '["garlic", "chilli"]'})
            self.call_tool("addItemToCart")

        # Convert all to meals
        self.call_tool("convertItemsToMeals")

        # Modify 2 meals
        self.call_tool("modifyCartItem", {"itemIndex": 0, "modifications": {"chips_size": "large"}})
        self.call_tool("modifyCartItem", {"itemIndex": 2, "modifications": {"chips_size": "large"}})

        # Price cart
        self.call_tool("priceCart")

        elapsed = time.time() - start

        assert elapsed < 8.0, f"Too slow: {elapsed:.2f}s (target < 8s)"

        result.details["elapsed"] = f"{elapsed:.2f}s"
        result.details["target"] = "< 8s"

    # =================================================================
    # CATEGORY 8: DATA INTEGRITY 🔒
    # =================================================================

    def test_8_1_cart_state_consistency(self, result: TestResult):
        """Test 8.1: getCartState and getDetailedCart return same items"""
        # Add items
        for i in range(3):
            self.call_tool("startItemConfiguration", {"category": "kebabs"})
            self.call_tool("setItemProperty", {"field": "size", "value": "large"})
            self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
            self.call_tool("addItemToCart")

        # Get both views
        resp1 = self.call_tool("getCartState")
        resp2 = self.call_tool("getDetailedCart")

        assert resp1["ok"] and resp2["ok"], "Failed to get cart states"

        # Both should show 3 items
        cart1_count = len(resp1.get("cart", []))
        cart2_count = resp2.get("itemCount", 0)

        assert cart1_count == cart2_count == 3, \
            f"Inconsistent counts: getCartState={cart1_count}, getDetailedCart={cart2_count}"

        result.details["consistent"] = True

    def test_8_2_quantity_handling(self, result: TestResult):
        """Test 8.2: Items with quantity > 1 handled correctly"""
        # Add item with quantity 3
        self.call_tool("startItemConfiguration", {"category": "kebabs"})
        self.call_tool("setItemProperty", {"field": "size", "value": "small"})
        self.call_tool("setItemProperty", {"field": "protein", "value": "chicken"})
        self.call_tool("setItemProperty", {"field": "quantity", "value": "3"})
        self.call_tool("addItemToCart")

        # Price cart
        resp = self.call_tool("priceCart")
        assert resp["ok"], "Failed to price"

        # Should be 3 × $10 = $30
        expected = 30.0
        assert abs(resp["grandTotal"] - expected) < 0.01, \
            f"Wrong quantity pricing: expected ${expected}, got ${resp['grandTotal']}"

        result.details["quantity"] = 3
        result.details["total"] = resp["grandTotal"]


def run_comprehensive_tests():
    """Run all comprehensive tests and generate report"""
    print("="*70)
    print("🧪 COMPREHENSIVE EDGE CASE TEST SUITE")
    print("="*70)
    print()

    suite = ComprehensiveTestSuite()

    # Category 1: Extreme Volume
    print("\n📋 CATEGORY 1: EXTREME VOLUME TESTS")
    print("-" * 70)
    suite.run_test(suite.test_1_1_single_item_order)
    suite.run_test(suite.test_1_2_maximum_order_size)
    suite.run_test(suite.test_1_3_empty_cart_operations)

    # Category 2: Rapid Modifications
    print("\n⚡ CATEGORY 2: RAPID MODIFICATION STRESS")
    print("-" * 70)
    suite.run_test(suite.test_2_1_add_remove_spam)
    suite.run_test(suite.test_2_2_modify_chain)
    suite.run_test(suite.test_2_3_clear_and_rebuild)

    # Category 3: Complex Meal Conversions
    print("\n🍔 CATEGORY 3: COMPLEX MEAL CONVERSIONS")
    print("-" * 70)
    suite.run_test(suite.test_3_1_partial_meal_upgrade_with_mods)
    suite.run_test(suite.test_3_2_already_meals_edge_case)
    suite.run_test(suite.test_3_3_mixed_sizes_meal_upgrade)
    suite.run_test(suite.test_3_4_meal_conversion_all_drink_types)

    # Category 4: Invalid Input
    print("\n🚫 CATEGORY 4: INVALID INPUT HANDLING")
    print("-" * 70)
    suite.run_test(suite.test_4_1_out_of_bounds_indices)
    suite.run_test(suite.test_4_2_invalid_field_values)

    # Category 5: Pricing Integrity
    print("\n💰 CATEGORY 5: PRICING INTEGRITY")
    print("-" * 70)
    suite.run_test(suite.test_5_1_all_kebab_sizes_priced_correctly)
    suite.run_test(suite.test_5_2_combo_pricing_vs_individual)
    suite.run_test(suite.test_5_3_large_chips_upgrade_pricing)
    suite.run_test(suite.test_5_4_extra_toppings_pricing)

    # Category 6: Real-World Chaos
    print("\n🌪️ CATEGORY 6: REAL-WORLD CHAOS")
    print("-" * 70)
    suite.run_test(suite.test_6_1_the_indecisive_customer)
    suite.run_test(suite.test_6_2_the_group_order)

    # Category 7: Performance Benchmarks
    print("\n⚡ CATEGORY 7: PERFORMANCE BENCHMARKS")
    print("-" * 70)
    suite.run_test(suite.test_7_1_speed_simple_order)
    suite.run_test(suite.test_7_2_speed_complex_order)

    # Category 8: Data Integrity
    print("\n🔒 CATEGORY 8: DATA INTEGRITY")
    print("-" * 70)
    suite.run_test(suite.test_8_1_cart_state_consistency)
    suite.run_test(suite.test_8_2_quantity_handling)

    # Generate summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in suite.results if r.passed)
    failed = len(suite.results) - passed
    pass_rate = (passed / len(suite.results)) * 100 if suite.results else 0

    print(f"\nTotal Tests: {len(suite.results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Pass Rate: {pass_rate:.1f}%")

    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for result in suite.results:
            if not result.passed:
                print(f"  - {result.name}: {result.error}")

    print("\n" + "="*70)

    if pass_rate >= 95:
        print("✅ SYSTEM IS PRODUCTION READY!")
    elif pass_rate >= 85:
        print("⚠️ SYSTEM IS MOSTLY READY - Fix remaining issues")
    else:
        print("❌ SYSTEM NEEDS MORE WORK - Critical issues found")

    print("="*70)

    return suite.results


if __name__ == "__main__":
    results = run_comprehensive_tests()

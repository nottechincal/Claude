# 🧪 Comprehensive Test Suite

## Overview

This test suite contains **25+ comprehensive edge case tests** across **8 categories** to ensure the VAPI ordering system is bulletproof.

## Test Categories

### 🔴 CRITICAL (Must Pass 100%)
1. **Extreme Volume Tests** - Single item, 20 items, empty cart handling
2. **Complex Meal Conversions** - Partial upgrades, mixed sizes, drink variations
3. **Pricing Integrity** - All menu items, combos, toppings, upgrades

### 🟡 HIGH PRIORITY (Must Pass 95%+)
4. **Invalid Input Handling** - Out of bounds, wrong types, graceful failures

### 🟢 MEDIUM PRIORITY (90%+ acceptable)
2. **Rapid Modification Stress** - Add/remove spam, modify chains, clear/rebuild
7. **Performance Benchmarks** - Simple < 3s, Complex < 8s

### 🔵 NICE-TO-HAVE (85%+ acceptable)
6. **Real-World Chaos** - Indecisive customer, group orders
8. **Data Integrity** - Cart consistency, quantity handling

---

## Prerequisites

### 1. **Server Must Be Running**

```bash
cd "C:\Users\aty.rwx\Documents\GitHub\Claude\Claude Latest"
python server_v2.py
```

**Expected output:**
```
Starting Kebabalab VAPI Server v2.0
...
Server ready to accept requests
```

### 2. **Install Dependencies**

```bash
pip install requests
```

---

## Running Tests

### Run All Tests

```bash
cd "C:\Users\aty.rwx\Documents\GitHub\Claude\Claude Latest\tests"
python test_comprehensive_edge_cases.py
```

### Expected Output

```
======================================================================
🧪 COMPREHENSIVE EDGE CASE TEST SUITE
======================================================================

📋 CATEGORY 1: EXTREME VOLUME TESTS
----------------------------------------------------------------------
✅ PASSED test_1_1_single_item_order (0.23s)
✅ PASSED test_1_2_maximum_order_size (2.45s)
✅ PASSED test_1_3_empty_cart_operations (0.18s)

⚡ CATEGORY 2: RAPID MODIFICATION STRESS
----------------------------------------------------------------------
✅ PASSED test_2_1_add_remove_spam (1.12s)
...

======================================================================
📊 TEST SUMMARY
======================================================================

Total Tests: 25
✅ Passed: 24
❌ Failed: 1
📈 Pass Rate: 96.0%

✅ SYSTEM IS PRODUCTION READY!
======================================================================
```

---

## Test Details

### Category 1: Extreme Volume Tests 🔢

**Test 1.1: Single Item Order**
- Simplest possible order (1 small kebab)
- Validates: Basic flow, pricing accuracy
- Expected: $10.00 total

**Test 1.2: Maximum Order Size**
- 20 large kebabs with unique modifications
- Validates: System handles large carts without crashing
- Expected: $300.00 total (20 × $15)

**Test 1.3: Empty Cart Operations**
- Try to price, convert, modify empty cart
- Validates: Graceful error handling
- Expected: Clear error messages, no crashes

---

### Category 2: Rapid Modification Stress ⚡

**Test 2.1: Add/Remove Spam**
- Add 5 kebabs, remove one, add 3 HSP, remove two, add 2 chips
- Validates: Cart index handling remains correct
- Expected: 8 final items, no orphaned data

**Test 2.2: Modify Chain**
- Chain 6 modifications on single item
- Validates: Multiple modifications work correctly
- Expected: Final state matches all changes

**Test 2.3: Clear and Rebuild**
- Add 10, clear, add 5, price, clear, add 1
- Validates: Session state clean after clears
- Expected: Final cart has only 1 item

---

### Category 3: Complex Meal Conversions 🍔

**Test 3.1: Partial Meal Upgrade with Mods** ⭐ **YOUR EXACT FAILING SCENARIO**
- Add 5 large kebabs
- Modify #1 and #3 with extra toppings
- Convert only #0, #2, #4 to meals
- Upgrade meal #2 to large chips
- Validates: Partial conversions, modifications preserved
- Expected: $100.00 total (2 regular + 3 meals, one with large chips)

**Test 3.2: Already-Meals Edge Case**
- Convert to meals twice
- Validates: Graceful handling of already-meals
- Expected: No crashes, appropriate handling

**Test 3.3: Mixed Sizes Meal Upgrade**
- 2 small + 3 large kebabs → all to meals
- Validates: Different meal prices applied correctly
- Expected: $100.00 (2×$17 + 3×$22)

**Test 3.4: All Drink Types**
- Convert 6 kebabs to meals with coke, sprite, fanta
- Validates: All drink types work, same pricing
- Expected: $132.00 (6×$22)

---

### Category 4: Invalid Input Handling 🚫

**Test 4.1: Out of Bounds Indices**
- Try to modify item 10 when only 3 exist
- Try negative indices
- Validates: Boundary checking
- Expected: Reject with clear errors

**Test 4.2: Invalid Field Values**
- Try "wagyu-gold" protein, "mega-ultra-large" size
- Validates: Menu validation (if implemented)
- Expected: Reject invalid values

---

### Category 5: Pricing Integrity 💰

**Test 5.1: All Kebab Sizes**
- Small kebab: $10, Large kebab: $15
- Validates: Base pricing correct
- Expected: Exact matches

**Test 5.2: Combo vs Individual**
- Kebab + chips + drink individually
- Validates: Combo detection saves money
- Expected: $17 combo (vs $18.50 individual)

**Test 5.3: Large Chips Upgrade**
- Small meal → upgrade to large chips
- Validates: Upgrade pricing logic
- Expected: $20 (not $17 + $9)

**Test 5.4: Extra Toppings**
- Cheese (+$1), Extra meat (+$3)
- Validates: Topping charges applied
- Expected: Correct additions

---

### Category 6: Real-World Chaos 🌪️

**Test 6.1: The Indecisive Customer** ⭐ **STRESS TEST**
- Changes mind 7 times during order
- Validates: System handles uncertainty
- Expected: Final state correct after all changes

**Test 6.2: The Group Order**
- 11 items with variations (3 kebabs, 2 kebabs, 1 HSP, 5 chips)
- Convert 2 to meals
- Validates: Complex multi-item orders
- Expected: Accurate total for all items

---

### Category 7: Performance Benchmarks ⚡

**Test 7.1: Speed - Simple Order**
- 1 item from start to price
- Validates: Basic operations are fast
- Target: < 3 seconds

**Test 7.2: Speed - Complex Order**
- 5 kebabs with mods → convert to meals → modify 2 → price
- Validates: Complex operations complete quickly
- Target: < 8 seconds

---

### Category 8: Data Integrity 🔒

**Test 8.1: Cart State Consistency**
- getCartState vs getDetailedCart
- Validates: Both return same data
- Expected: Consistent item counts

**Test 8.2: Quantity Handling**
- Add item with quantity=3
- Validates: Quantity multiplies price correctly
- Expected: 3 × $10 = $30

---

## Success Criteria

**Production Ready When:**
- ✅ Categories 1, 3, 5 pass at 100%
- ✅ Categories 4 passes at 95%+
- ✅ Categories 2, 7 pass at 90%+
- ✅ Categories 6, 8 pass at 85%+
- ✅ Zero crashes on any test
- ✅ Zero pricing errors

---

## Interpreting Results

### ✅ **Pass Rate ≥ 95%**
**Status:** PRODUCTION READY
**Action:** Deploy to production immediately

### ⚠️ **Pass Rate 85-94%**
**Status:** MOSTLY READY
**Action:** Review failed tests, fix critical issues only

### ❌ **Pass Rate < 85%**
**Status:** NEEDS WORK
**Action:** Fix all failed tests before deploying

---

## Common Issues

### Issue: "Connection refused"
**Cause:** Server not running
**Fix:** Start server with `python server_v2.py`

### Issue: "Test timeout"
**Cause:** Server is frozen or crashed
**Fix:** Restart server

### Issue: "Wrong pricing"
**Cause:** Menu prices changed or bug in calculation
**Fix:** Check menu.json matches hardcoded prices

---

## Next Steps After Tests Pass

1. ✅ **Commit test results** to git
2. ✅ **Restart production server** with fixes
3. ✅ **Test with real calls** on production number
4. ✅ **Monitor call logs** for 24 hours
5. ✅ **Celebrate** - system is bulletproof! 🎉

---

**Last Updated:** 2025-10-22
**Test Count:** 25 tests
**Coverage:** 8 categories

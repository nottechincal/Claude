# 🧪 Comprehensive Edge Case Test Plan
**Status:** PENDING APPROVAL
**Date:** October 22, 2025

---

## 🎯 Testing Philosophy

**Goal:** Make this system BULLETPROOF - able to handle ANY customer scenario without breaking.

**Standards:**
- Every test must simulate REAL customer behavior
- Cover both happy paths AND chaos scenarios
- Test system recovery from errors
- Validate pricing accuracy in ALL cases
- Ensure no data corruption under stress

---

## 📋 Test Categories

### **Category 1: Extreme Volume Tests** 🔢

**Why:** System must handle both tiny and massive orders

#### Test 1.1: Single Item Order
- Add 1 small chicken kebab
- Complete order
- **Validate:** Pricing, SMS sent, DB record created

#### Test 1.2: Maximum Order Size
- Add 20 large kebabs with unique modifications
- Convert all to meals
- Complete order
- **Validate:**
  - System doesn't crash
  - Pricing accurate for all 20 items
  - Cart state maintained
  - Total calculation correct

#### Test 1.3: Empty Cart Operations
- Try to price empty cart
- Try to convert empty cart to meals
- Try to modify item in empty cart
- **Validate:** Graceful error messages, no crashes

---

### **Category 2: Rapid Modification Stress** ⚡

**Why:** Customer changes mind rapidly, system must keep up

#### Test 2.1: Add/Remove Spam
```
1. Add 5 kebabs
2. Remove item 0
3. Add 3 HSP
4. Remove item 2
5. Remove item 4
6. Add 2 chips
7. Remove all chips
8. Convert remaining to meals
```
**Validate:** Cart indices stay correct, no orphaned items

#### Test 2.2: Modify Chain
```
1. Add large chicken kebab
2. Modify size to small
3. Modify protein to lamb
4. Modify protein to mixed
5. Modify size back to large
6. Convert to meal
7. Modify meal chips to large
```
**Validate:** Final state matches ALL modifications

#### Test 2.3: Clear and Rebuild
```
1. Add 10 items
2. Clear cart
3. Immediately add 5 new items
4. Price cart
5. Clear cart again
6. Add 1 item
7. Complete order
```
**Validate:** Session state clean, no ghost items

---

### **Category 3: Complex Meal Conversions** 🍔

**Why:** Meal upgrades are the most complex operation

#### Test 3.1: Partial Meal Upgrade with Modifications
```
1. Add 5 large chicken kebabs
2. Modify kebabs #1, #3 to have extra toppings
3. Convert only #0, #2, #4 to meals
4. Modify meal #2 to have large chips
5. Price cart
```
**Validate:**
- Items 0, 2, 4 are meals
- Items 1, 3 are still regular kebabs
- Extra toppings preserved on #1, #3
- Large chips upgrade priced correctly

#### Test 3.2: Already-Meals Edge Case
```
1. Add 3 kebabs
2. Convert all to meals
3. Try to convert to meals AGAIN
```
**Validate:** Graceful handling, no double-meals

#### Test 3.3: Mixed Sizes Meal Upgrade
```
1. Add 2 small kebabs
2. Add 3 large kebabs
3. Convert all to meals (default small chips)
4. Upgrade 2 large kebab meals to have large chips
```
**Validate:**
- 2 small kebab meals = $17 each
- 3 large kebab meals with small chips = $22 each
- 2 large kebab meals with large chips = $25 each
- Total: $34 + $66 + $50 = $150

#### Test 3.4: Meal Conversion with All Drink Types
```
1. Add 6 large kebabs
2. Convert items 0,1 to meals (coke)
3. Convert items 2,3 to meals (sprite)
4. Convert items 4,5 to meals (fanta)
```
**Validate:** Each meal has correct drink, pricing identical

---

### **Category 4: Invalid Input Handling** 🚫

**Why:** System must reject garbage gracefully

#### Test 4.1: Out of Bounds Indices
```
1. Add 3 kebabs
2. Try to modify item index 10 (doesn't exist)
3. Try to remove item index -1 (negative)
4. Try to convert item indices [0, 2, 99] to meals
```
**Validate:** Clear error messages, cart unchanged

#### Test 4.2: Invalid Field Values
```
1. Add kebab
2. Try to modify with invalid protein "wagyu-gold"
3. Try to set size to "mega-ultra-large"
4. Try to set salads to "pineapple, chocolate, ice cream"
```
**Validate:** Menu validation rejects, helpful error messages

#### Test 4.3: Missing Required Fields
```
1. Start item configuration with no category
2. Add item to cart with incomplete data
3. Try to create order with no customer name
```
**Validate:** Validation catches all missing fields

#### Test 4.4: Type Mismatches
```
1. Send itemIndex as string "three" instead of number 3
2. Send salads as string "lettuce" instead of array ["lettuce"]
3. Send quantity as "lots" instead of number
```
**Validate:** Type validation, graceful conversion or rejection

---

### **Category 5: Pricing Integrity** 💰

**Why:** Cannot lose money from pricing bugs

#### Test 5.1: All Menu Items Priced Correctly
```
For each category (kebabs, hsp, chips, drinks):
  For each size (small, large):
    For each protein (lamb, chicken, mixed, falafel):
      - Add item
      - Price cart
      - Validate against menu.json
```
**Validate:** 100% pricing accuracy

#### Test 5.2: Combo Pricing vs Individual
```
1. Add kebab ($15) + chips ($5) + drink ($3.50) = $23.50
2. Price cart
3. Validate combo detected: $17 (save $6.50)

4. Add large kebab ($20) + chips ($5) + drink ($3.50) = $28.50
5. Validate combo: $22 (save $6.50)
```

#### Test 5.3: Large Chips Upgrade Pricing
```
1. Add small kebab meal ($17)
2. Upgrade chips to large
3. Validate price: $20 (not $17 + $9)

4. Add large kebab meal ($22)
5. Upgrade chips to large
6. Validate price: $25 (not $22 + $9)
```

#### Test 5.4: Extra Toppings Pricing
```
1. Add kebab with cheese (+$1)
2. Add kebab with extra meat (+$3)
3. Add kebab with both cheese and extra meat
4. Validate totals: base + $1, base + $3, base + $4
```

---

### **Category 6: Concurrent Operations** 🔄

**Why:** Multiple customers calling simultaneously

#### Test 6.1: Two Sessions Isolated
```
Session A (+61 400 000 001):
  1. Add 3 kebabs
  2. Start configuring HSP

Session B (+61 400 000 002):
  1. Add 5 chips
  2. Complete order

Session A:
  3. Complete order

Validate:
  - Session A has 3 kebabs + 1 HSP
  - Session B has 5 chips
  - No cross-contamination
```

#### Test 6.2: Rapid Session Switches
```
1. Start 10 concurrent sessions
2. Each adds 1-10 random items
3. All price carts simultaneously
4. All complete orders
5. Validate: 10 distinct orders in DB, no mixing
```

---

### **Category 7: Real-World Chaos** 🌪️

**Why:** Customers are unpredictable

#### Test 7.1: The Indecisive Customer
```
Customer: "5 chicken kebabs"
[Adds 5 chicken kebabs]

Customer: "Actually make them lamb"
[Modifies all to lamb]

Customer: "No wait, 3 chicken, 2 lamb"
[Modifies #0,#1,#2 back to chicken]

Customer: "Make them all meals"
[Converts all to meals]

Customer: "Actually just 3 meals, remove 2"
[Removes items #3, #4]

Customer: "Add large chips to all meals"
[Upgrades chips on remaining 3 meals]

Customer: "Change drinks to sprite"
[Modifies all meal drinks]

Complete order
```
**Validate:** Final cart matches last state, pricing correct

#### Test 7.2: The Detail-Obsessed Customer
```
"Large chicken kebab with lettuce, tomato, onion, cheese,
garlic sauce, chilli sauce, BBQ sauce, extra meat, no tabouli"

Add item
Validate: All 9 modifiers applied correctly
```

#### Test 7.3: The Group Order
```
"3 small lamb kebabs - first one no onion, second one extra cheese,
third one plain. 2 large chicken kebabs - both with everything.
1 large HSP with mixed meat. 5 small chips - 2 chicken salt, 2 plain,
1 seasoned. 3 cokes and 2 sprites."

Add all items
Convert 2 kebabs to meals
Complete order

Validate:
- 12 distinct items
- Modifications preserved
- Correct meal conversions
- Total accurate
```

---

### **Category 8: Error Recovery** 🛡️

**Why:** System must recover from failures

#### Test 8.1: Database Error During Order
```
1. Add items to cart
2. Simulate DB connection failure
3. Try to create order
4. Validate: Error returned, cart NOT cleared
5. Restore DB connection
6. Create order successfully
7. Validate: Order saved correctly
```

#### Test 8.2: SMS Failure Handling
```
1. Complete order with invalid Twilio credentials
2. Validate:
   - Order still saved to DB
   - Error logged
   - System continues
```

#### Test 8.3: Session Expiry Mid-Order
```
1. Add 5 items
2. Wait 16 minutes (session expires)
3. Try to complete order
4. Validate: Clear error "Session expired, please start over"
```

---

### **Category 9: Performance Benchmarks** ⚡

**Why:** Calls must be fast to reduce costs

#### Test 9.1: Speed Test - Simple Order
```
Start timer
1. Add 1 kebab
2. Add to cart
3. Price cart
4. Complete order
End timer

Target: < 3 seconds total
```

#### Test 9.2: Speed Test - Complex Order
```
Start timer
1. Add 5 kebabs with modifications
2. Convert all to meals
3. Modify 2 meals
4. Price cart
5. Complete order
End timer

Target: < 8 seconds total
```

#### Test 9.3: Tool Call Count
```
Track number of tool calls for:
- Simple order (1 item): Target < 5 calls
- Medium order (5 items): Target < 15 calls
- Complex order (10 items + mods): Target < 25 calls
```

---

### **Category 10: Data Integrity** 🔒

**Why:** Database must stay clean

#### Test 10.1: Order Record Completeness
```
1. Create order with all fields populated
2. Query database
3. Validate:
   - customer_name
   - customer_phone
   - cart (full JSON)
   - totals (full JSON)
   - pickup_time
   - delivery_type
   - special_notes
   - payment_method
   - created_at timestamp
```

#### Test 10.2: Phone Number Normalization
```
Test these phone formats all map to same customer:
- "0412 345 678"
- "+61412345678"
- "61412345678"
- "0412-345-678"

Validate: All create/fetch same customer record
```

#### Test 10.3: Cart State Consistency
```
1. Add items
2. Getdetailed cart
3. Compare with getCartState
4. Validate: Both return same items, same pricing
```

---

## 🚀 Test Execution Plan

### Phase 1: Core Functionality (Priority: CRITICAL)
- Categories 1, 3, 5 (Volume, Meals, Pricing)
- **ETA:** 2-3 hours to implement
- **Must Pass:** 100% before production

### Phase 2: Error Handling (Priority: HIGH)
- Categories 4, 8 (Invalid Input, Recovery)
- **ETA:** 1-2 hours to implement
- **Must Pass:** 95% before production

### Phase 3: Stress & Performance (Priority: MEDIUM)
- Categories 2, 6, 9 (Modifications, Concurrent, Performance)
- **ETA:** 2-3 hours to implement
- **Must Pass:** 90% acceptable

### Phase 4: Real-World Chaos (Priority: NICE-TO-HAVE)
- Categories 7, 10 (Chaos, Data Integrity)
- **ETA:** 1-2 hours to implement
- **Must Pass:** 85% acceptable

---

## 📊 Success Criteria

**System is production-ready when:**
- ✅ All Category 1, 3, 5 tests pass (100%)
- ✅ Category 4, 8 tests pass (95%+)
- ✅ Category 2, 6, 9 tests pass (90%+)
- ✅ Category 7, 10 tests pass (85%+)
- ✅ Zero crashes on invalid input
- ✅ Zero pricing errors
- ✅ Zero data corruption

---

## 🔧 Test Implementation

Each test will:
1. **Use direct server API calls** (bypass VAPI for speed)
2. **Verify response structure** (ok, error messages)
3. **Check pricing accuracy** (compare to menu.json)
4. **Validate cart state** (items, quantities, modifications)
5. **Assert database integrity** (orders table)
6. **Measure performance** (execution time)

---

## 📝 Test Report Format

For each test:
```
✅ Test 3.1: Partial Meal Upgrade with Modifications
   - Items tested: 5 kebabs → 3 meals, 2 regular
   - Pricing: $66 + $30 = $96 ✅
   - Modifications preserved: ✅
   - Cart state consistent: ✅
   - Execution time: 2.3 seconds
   - Status: PASSED

❌ Test 4.2: Invalid Field Values
   - Expected: Reject "wagyu-gold" protein
   - Actual: Accepted without validation
   - Status: FAILED - Menu validation needed
```

---

## 🎯 Questions for Approval

Before I implement these tests, please confirm:

1. **Are these test scenarios realistic?** Any customer behaviors I'm missing?
2. **Should I add more stress tests?** (e.g., 50-item orders, 100 concurrent users)
3. **Performance targets acceptable?** (3 sec simple, 8 sec complex orders)
4. **Any specific edge cases from YOUR production calls?** (What broke yesterday?)
5. **Test priority order correct?** (Pricing/Meals first, then error handling, then stress)

---

**Total Estimated Tests:** ~60-80 individual test cases
**Implementation Time:** 6-10 hours
**Execution Time:** ~5-10 minutes for full suite

**Status:** ⏸️ AWAITING YOUR APPROVAL TO PROCEED

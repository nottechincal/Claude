# 🧪 Testing Scenarios - Kebabalab VAPI System

## Test these scenarios to ensure the system works correctly

---

## Scenario 1: Simple Kebab Order

**Customer Says:**
```
"I'll get a small chicken kebab please."
```

**Expected System Flow:**
1. ✅ `startItemConfiguration { category: "kebabs", name: "Chicken Kebab" }`
2. ✅ `setItemProperty { field: "size", value: "small" }`
3. ✅ `setItemProperty { field: "protein", value: "chicken" }`
4. 🗣️ "What salads would you like?"

**Customer:** "Lettuce, tomato, onion"

5. ✅ `setItemProperty { field: "salads", value: ["lettuce", "tomato", "onion"] }`
6. 🗣️ "And which sauces?"

**Customer:** "Garlic and chilli"

7. ✅ `setItemProperty { field: "sauces", value: ["garlic", "chilli"] }`
8. 🗣️ "Would you like to add cheese or any extras?"

**Customer:** "No thanks"

9. ✅ `setItemProperty { field: "extras", value: [] }`
10. ✅ `addItemToCart {}`
11. 🗣️ "Got it! Anything else?"

**Expected Result:**
- Item added to cart with all properties
- No combo detected (kebab alone)

---

## Scenario 2: Kebab + Can → Auto Combo

**Customer Says:**
```
"Small lamb kebab and a Coke please."
```

**Expected System Flow:**

**For Kebab:**
1. Configure kebab (size, protein, salads, sauces)
2. `addItemToCart {}`

**For Drink:**
3. `startItemConfiguration { category: "drinks" }`
4. `setItemProperty { field: "brand", value: "coca-cola" }`
5. `addItemToCart {}`

**Expected Response from addItemToCart:**
```json
{
  "ok": true,
  "comboDetected": true,
  "comboInfo": {
    "name": "Small Kebab & Can Combo",
    "savings": 1.5
  }
}
```

**System Should Say:**
🗣️ "I've made that a Small Kebab & Can Combo for you!"

**Expected Cart:**
- 1 combo item (not 2 separate items)
- Price: $12.00

---

## Scenario 3: Kebab Meal (Kebab + Chips + Can)

**Customer Says:**
```
"Large chicken kebab, small chips, and a Sprite."
```

**Expected System Flow:**

1. Configure and add kebab
2. Configure and add chips (default chicken salt)
3. Configure and add drink

**Expected Combo Detection:**
After drink added:
```json
{
  "comboDetected": true,
  "comboInfo": {
    "name": "Large Kebab Meal",
    "savings": 1.5
  }
}
```

**System Should Say:**
🗣️ "I've made that a Large Kebab Meal for you!"

**Expected Cart:**
- 1 meal combo
- Price: $22.00
- Includes: large kebab details + small chips (chicken salt) + Sprite

---

## Scenario 4: Large Kebab Meal with Large Chips

**Customer Says:**
```
"Large lamb kebab, large chips, and a Fanta."
```

**Expected Combo:**
- "Large Kebab Meal with Large Chips"
- Price: $25.00
- Savings: $2.50

---

## Scenario 5: HSP + Can → Auto Combo

**Customer Says:**
```
"Small chicken HSP and a Coke please."
```

**Expected System Flow:**

**For HSP:**
1. Confirm size: small
2. Confirm protein: chicken
3. Ask sauces: "Which sauces?"
4. Ask cheese: "Would you like cheese?"
5. Add to cart

**For Drink:**
6. Add Coke

**Expected Combo:**
```json
{
  "comboDetected": true,
  "comboInfo": {
    "name": "Small HSP Combo",
    "savings": 1.5
  }
}
```

**Price:** $17.00

---

## Scenario 6: Multiple Items (No Combo)

**Customer Says:**
```
"Two small lamb kebabs and a large chips."
```

**Expected System Flow:**

1. Configure first kebab
2. `setItemProperty { field: "quantity", value: 2 }`
3. Add to cart
4. Configure chips
5. Add to cart

**Expected:**
- NO combo detected (no drink)
- Cart: 2 items (kebabs, chips)
- Price: 2×$10 + $9 = $29.00

---

## Scenario 7: No Salads, No Sauces

**Customer Says:**
```
"Small chicken kebab, no salads, no sauces."
```

**Expected System Flow:**
1. Start configuration
2. Confirm size and protein
3. Ask salads → Customer says "no salads"
4. `setItemProperty { field: "salads", value: [] }`
5. Ask sauces → Customer says "no sauces"
6. `setItemProperty { field: "sauces", value: [] }`
7. Add to cart

**Expected Cart Item:**
```json
{
  "category": "kebabs",
  "size": "small",
  "protein": "chicken",
  "salads": [],
  "sauces": [],
  "extras": []
}
```

---

## Scenario 8: Chips with Custom Salt

**Customer Says:**
```
"Large chips with normal salt."
```

**Expected System Flow:**
1. `startItemConfiguration { category: "chips" }`
2. `setItemProperty { field: "size", value: "large" }`
3. `setItemProperty { field: "salt_type", value: "normal" }`
4. `addItemToCart {}`

**Expected Cart:**
```json
{
  "category": "chips",
  "size": "large",
  "salt_type": "normal"
}
```

**If customer doesn't mention salt:**
- Default to `"salt_type": "chicken"`

---

## Scenario 9: Extras (Cheese, Extra Meat)

**Customer Says:**
```
"Small lamb kebab with extra lamb and cheese."
```

**Expected System Flow:**
1. Configure kebab
2. When asked about extras:
   - `setItemProperty { field: "extras", value: ["extra lamb", "cheese"] }`

**Expected Pricing:**
- Base: $10
- Extra lamb: +$3
- Cheese: +$1
- **Total: $14**

---

## Scenario 10: Complete Order with Checkout

**Full Order:**
```
Customer: "Small chicken kebab, small chips, and a Coke."
```

**Expected Flow:**

1-10. Configure and add items (forms combo)
11. 🗣️ "I've made that a Small Kebab Meal for you! Anything else?"
12. Customer: "No, that's all."
13. ✅ `priceCart {}`
14. 🗣️ "Your total is $17."
15. 🗣️ "Can I get a name for the order?"
16. Customer: "Sarah"
17. ✅ `estimateReadyTime {}`
18. 🗣️ "Your order will be ready in about 15 minutes."
19. ✅ `createOrder { customerName: "Sarah", customerPhone: "...", readyAtIso: "..." }`
20. 🗣️ "Perfect! Your order number is 001. See you in 15 minutes!"
21. ✅ `endCall {}`

**Expected Database:**
- Order created with ID like `20251021-001`
- Cart stored as JSON
- Customer details saved

---

## Scenario 11: Customer Asks About Combo Savings

**Customer Says:**
```
"How much do I save with the meal?"
```

**System Should:**
- Reference `comboInfo.savings` from previous combo detection
- Say: "That saves you $1.50!"

---

## Scenario 12: Edge Case - Adding Can Last Creates Combo

**Customer Says:**
```
"Small lamb kebab" → configure → add
"Small chips" → configure → add
"Actually, add a Coke too"
```

**Expected:**
- When Coke is added, system detects kebab + chips + can
- Converts to "Small Kebab Meal"
- Announces: "I've made that a Small Kebab Meal for you!"

---

## Scenario 13: No Caller ID - Ask for Phone

**Situation:** `getCallerInfo` returns `hasCallerID: false`

**Expected Flow:**
- Take order normally
- At checkout, when need phone:
  - 🗣️ "And a contact number?"
  - Customer provides number
  - Use that in `createOrder`

---

## Test Checklist

### Basic Functionality
- [ ] Kebab order with all confirmations (size, protein, salads, sauces)
- [ ] HSP order with all confirmations
- [ ] Chips order (default chicken salt)
- [ ] Drinks order (brand selection)

### Combo Detection
- [ ] Small Kebab + Can → $12 combo
- [ ] Large Kebab + Can → $17 combo
- [ ] Small Kebab + Small Chips + Can → $17 meal
- [ ] Large Kebab + Small Chips + Can → $22 meal
- [ ] Large Kebab + Large Chips + Can → $25 meal
- [ ] Small HSP + Can → $17 combo
- [ ] Large HSP + Can → $22 combo

### Edge Cases
- [ ] No salads, no sauces
- [ ] Multiple quantities
- [ ] Custom salt type
- [ ] Extras (cheese, extra meat)
- [ ] No caller ID
- [ ] Items added in different order still creates combo

### Checkout Flow
- [ ] Price calculation correct
- [ ] Customer name collected
- [ ] Phone number from caller ID
- [ ] Ready time estimated
- [ ] Order created in database
- [ ] Call ends gracefully

---

## Validation Points

### After Each Test:

1. **Check Server Logs:**
```bash
tail -f kebabalab_server.log | grep ERROR
```

2. **Check Database:**
```bash
sqlite3 orders.db "SELECT order_id, customer_name, totals FROM orders ORDER BY created_at DESC LIMIT 1;"
```

3. **Verify Cart State:**
- Call `getCartState {}` at any point
- Confirm items match expected

4. **Verify Pricing:**
- Cart total should match menu prices
- Combo pricing should be applied
- Extras should add correctly

---

## Common Issues & Fixes

### Issue: Combo not detected
**Fix:** Check cart items have correct `category` and `size` fields

### Issue: Tool returns error
**Fix:** Check server logs for stack trace, verify parameters

### Issue: Assistant skips confirmation
**Fix:** Review system prompt, ensure strict flow adherence

### Issue: Wrong default used
**Fix:** Verify menu.json has empty defaults, check prompt doesn't assume

---

**Run through all scenarios before going live!** 🚀

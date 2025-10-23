# System Simplification Design

## Problem Statement

Current system has 22 tools with significant overlap causing:
- AI confusion about which tool to use
- Loop bugs (20+ ModifyCartItem calls for simple chip upgrade)
- Slow performance (multiple calls for single actions)
- Over-engineered complexity

## Solution: 15 Focused Tools

### Core Principle
**One tool, one clear purpose. Zero overlap.**

---

## The 15 Tools

### 1. checkOpen
**Purpose:** Check if shop is open
**Keep/Remove:** KEEP (essential)
**Changes:** None

### 2. getCallerSmartContext
**Purpose:** Get caller phone + order history + favorites
**Keep/Remove:** KEEP (replaces basic getCallerInfo)
**Changes:** This is the ONLY context tool
**Replaces:**
- getCallerInfo (basic)

### 3. quickAddItem
**Purpose:** NLP parser - add items from natural language
**Keep/Remove:** KEEP (speed optimization)
**Changes:** Make it handle complex descriptions better
**Examples:**
- "large lamb kebab with garlic sauce and lettuce"
- "2 cokes"
- "small chicken hsp no salad"
**Replaces:**
- startItemConfiguration
- setItemProperty (multiple calls)
- addItemToCart

### 4. addMultipleItemsToCart
**Purpose:** Batch add fully configured items
**Keep/Remove:** KEEP (speed optimization)
**Changes:** None
**Use case:** When customer lists multiple items upfront

### 5. getCartState
**Purpose:** View current cart contents
**Keep/Remove:** KEEP + ENHANCE
**Changes:** Return both structured data AND human-readable format
**Replaces:**
- getCartState (raw data)
- getDetailedCart (formatted)

### 6. removeCartItem
**Purpose:** Remove item from cart by index
**Keep/Remove:** KEEP
**Changes:** None

### 7. editCartItem
**Purpose:** Edit ANY property of cart item in ONE call
**Keep/Remove:** CONSOLIDATE
**Changes:** Can now modify ANYTHING (size, protein, salads, sauces, chips_size, etc.)
**Critical:** Must work in ONE call
**Replaces:**
- editCartItem (limited)
- modifyCartItem (full)

**Examples:**
```json
editCartItem(0, {"chips_size": "large"}) → Done in 1 call
editCartItem(0, {"size": "large", "sauces": ["garlic", "chili"]}) → Done in 1 call
```

### 8. priceCart
**Purpose:** Calculate total with breakdown
**Keep/Remove:** KEEP
**Changes:** None

### 9. convertItemsToMeals
**Purpose:** Convert kebabs to meals (kebab + chips + drink)
**Keep/Remove:** KEEP
**Changes:** None

### 10. getOrderSummary
**Purpose:** Get human-readable order summary for review
**Keep/Remove:** KEEP
**Changes:** None

### 11. setPickupTime
**Purpose:** Set custom pickup time when customer requests specific time
**Keep/Remove:** ADD (currently missing)
**Changes:** New tool
**Use case:** "I'll pick it up at 6pm"

### 12. estimateReadyTime
**Purpose:** Estimate ready time based on queue
**Keep/Remove:** KEEP
**Changes:** None

### 13. createOrder
**Purpose:** Create and save final order
**Keep/Remove:** KEEP
**Changes:** Accept optional notes parameter (eliminates setOrderNotes)

### 14. repeatLastOrder
**Purpose:** Copy customer's last order to cart
**Keep/Remove:** KEEP
**Changes:** None
**Replaces:**
- getLastOrder + addItemToCart loop

### 15. endCall
**Purpose:** End call gracefully
**Keep/Remove:** KEEP
**Changes:** None

---

## Tools Being REMOVED

### validateMenuItem
**Why remove:** Not needed - menu validation happens automatically in quickAddItem/addMultipleItemsToCart

### getMenuByCategory
**Why remove:** AI should know menu from system prompt, not query it

### getCallerInfo
**Why remove:** Replaced by getCallerSmartContext (enhanced version)

### startItemConfiguration + setItemProperty + addItemToCart
**Why remove:** Replaced by quickAddItem (1 call instead of 5-10 calls)

### modifyCartItem
**Why remove:** Merged into editCartItem

### getDetailedCart
**Why remove:** Merged into getCartState

### clearCart
**Why remove:** Rarely used, can use removeCartItem in loop if needed

### clearSession
**Why remove:** Not needed in production

### setOrderNotes
**Why remove:** Notes parameter added to createOrder

### getLastOrder
**Why remove:** Replaced by repeatLastOrder (does both get + add)

### lookupOrder
**Why remove:** Out of scope for new order system

### sendMenuLink
**Why remove:** Out of scope for phone orders

---

## Performance Improvements

### Current Flow (Add item):
1. startItemConfiguration
2. setItemProperty (size)
3. setItemProperty (protein)
4. setItemProperty (salads)
5. setItemProperty (sauces)
6. addItemToCart

**= 6 tool calls**

### New Flow (Add item):
1. quickAddItem("large lamb kebab with garlic sauce and lettuce")

**= 1 tool call = 83% faster**

---

### Current Flow (Modify chips size):
1. modifyCartItem → try
2. modifyCartItem → try again
3. modifyCartItem → loop
... (x20)
Customer hangs up

**= BROKEN**

### New Flow (Modify chips size):
1. editCartItem(0, {"chips_size": "large"})

**= 1 tool call = WORKS**

---

## Implementation Plan

### Phase 1: Core Server
1. Create `server_simplified.py`
2. Implement 15 tools with clear logic
3. Test each tool in isolation

### Phase 2: Enhanced Tools
1. **editCartItem**: Support ALL fields in one call
2. **getCartState**: Return both structured + formatted
3. **quickAddItem**: Robust NLP parsing
4. **setPickupTime**: New tool for custom times

### Phase 3: Testing
1. Test exact scenario from bug log (chip upgrade)
2. Test all 15 tools independently
3. Test complete order flows
4. Performance benchmarks

### Phase 4: VAPI Integration
1. Create vapi-tools-simplified.json (15 tools)
2. Update system prompt for simplified flow
3. Deploy and test

---

## Success Criteria

- ✅ Chip size upgrade works in 1 call (not 20+)
- ✅ Complete order in <10 tool calls (currently 20-30)
- ✅ Zero tool overlap/confusion
- ✅ All functionality preserved
- ✅ Faster, simpler, more reliable

---

## Next Steps

1. Build `server_simplified.py`
2. Test chip upgrade scenario
3. Full regression testing
4. Deploy

**This will work.**

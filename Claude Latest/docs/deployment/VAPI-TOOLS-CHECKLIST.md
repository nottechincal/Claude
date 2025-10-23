# 🛠️ VAPI Dashboard Tools - Complete List

## Total Tools: **26 Tools**

You should have **26 tools** in your VAPI dashboard.

---

## ✅ Core Tools (Already Have - 20 tools)

These were in your original system:

1. **startItemConfiguration** - Start building an item
2. **setItemProperty** - Set item properties (size, protein, salads, etc.)
3. **addItemToCart** - Add configured item to cart
4. **getCartState** - View current cart contents
5. **priceCart** - Calculate cart total
6. **checkOpen** - Check if restaurant is open
7. **getCallerInfo** - Get customer phone/name
8. **setPickupTime** - Set order pickup time
9. **estimateReadyTime** - Estimate when order will be ready
10. **getOrderSummary** - Get summary of current order
11. **setOrderNotes** - Add special notes to order
12. **getLastOrder** - Get customer's previous order
13. **lookupOrder** - Look up order by ID
14. **sendMenuLink** - Send menu link via SMS
15. **createOrder** - Finalize and create order
16. **removeCartItem** - Remove item from cart
17. **editCartItem** - Edit existing cart item (LIMITED - only salads/sauces)
18. **clearCart** - Clear entire cart
19. **clearSession** - Clear customer session
20. **endCall** - End call and cleanup

---

## 🆕 NEW Tools (Must Add - 6 tools)

These are the NEW tools from the fixes:

### Cart Management Fixes (3 tools)

21. **convertItemsToMeals** ⭐ **CRITICAL - Fixes your 5 kebab issue!**
22. **modifyCartItem** - Unrestricted cart modifications
23. **getDetailedCart** - Human-readable cart descriptions

### Essential Features (3 tools)

24. **validateMenuItem** - Validate menu items exist
25. **repeatLastOrder** - Fast reorder for regulars
26. **getMenuByCategory** - Browse menu by category

---

## 📋 Which Tools You Said You Added

You said you already added these **3 tools**:
- ✅ convertItemsToMeals
- ✅ modifyCartItem
- ✅ getDetailedCart

**So you're missing 3 more:**
- ❌ validateMenuItem
- ❌ repeatLastOrder
- ❌ getMenuByCategory

---

## 🚨 **ACTION REQUIRED: Add 3 Missing Tools**

### Tool 24: validateMenuItem

```json
{
  "type": "function",
  "function": {
    "name": "validateMenuItem",
    "description": "Validate that menu item exists and has valid properties before adding to cart",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "category": {
          "type": "string",
          "description": "Category: kebabs, hsp, chips, drinks, etc."
        },
        "size": {
          "type": "string",
          "description": "Size: small or large"
        },
        "protein": {
          "type": "string",
          "description": "Protein: lamb, chicken, mixed, falafel"
        }
      },
      "required": ["category"]
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

### Tool 25: repeatLastOrder

```json
{
  "type": "function",
  "function": {
    "name": "repeatLastOrder",
    "description": "Copy customer's last order to current cart for fast reordering. Use when customer says 'my usual' or 'same as last time'",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "phoneNumber": {
          "type": "string",
          "description": "Customer phone number"
        }
      },
      "required": ["phoneNumber"]
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

### Tool 26: getMenuByCategory

```json
{
  "type": "function",
  "function": {
    "name": "getMenuByCategory",
    "description": "Get menu items by category or list all categories. Use when customer asks 'what do you have' or 'what kebabs are there'",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "category": {
          "type": "string",
          "description": "Category name (kebabs, hsp, chips, drinks). Leave empty to list all categories"
        }
      }
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

## 📝 Summary

### You Currently Have:
- ✅ 20 original tools
- ✅ 3 cart management tools (convertItemsToMeals, modifyCartItem, getDetailedCart)

### You Need to Add:
- ❌ validateMenuItem
- ❌ repeatLastOrder
- ❌ getMenuByCategory

**Total after adding:** 26 tools

---

## 🔍 Menu.json Status

### ✅ Menu.json is CORRECT!

I checked your menu.json and the prices are accurate:
- ✅ **Large chips:** $9.00 (correct)
- ✅ **Small chips:** $5.00 (correct)
- ✅ **Kebab meals:** $17 small, $22 large (correct)

### ⚠️ One Issue Found:

**Individual soft drink pricing is NOT in menu.json**

Your menu.json has:
- ✅ Drink brands listed (coke, sprite, fanta, etc.)
- ❌ NO individual price for standalone drinks

**Current workaround:** server_v2.py has hardcoded $3.50 for drinks (which I fixed from $3.00)

**Recommendation:** Add individual drink pricing to menu.json:

```json
{
  "id": "DRK_CAN",
  "name": "Soft Drink Can (375ml)",
  "price": 3.5,   ← ADD THIS LINE
  "brands": [
    "coca-cola",
    "coke zero",
    ...
  ]
}
```

But this is NOT critical - the hardcoded price in server_v2.py works fine.

---

## ✅ What to Do Now

### Step 1: Add 3 Missing Tools to VAPI
Copy the JSON above for tools 24, 25, 26 into your VAPI dashboard

### Step 2: Restart Server
```bash
cd "C:\Users\aty.rwx\Documents\GitHub\Claude\Claude Latest"
python server_v2.py
```

### Step 3: Run Tests
```bash
cd tests
python test_comprehensive_edge_cases.py
```

---

**After adding the 3 tools, you'll have all 26 tools and the system will be complete!**

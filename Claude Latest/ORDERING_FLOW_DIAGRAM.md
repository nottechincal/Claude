# Kebabalab VAPI Ordering System - Complete Flow Diagram

**Generated:** 2025-10-29
**Purpose:** Visual representation of how orders flow through the system

---

## 🎯 System Overview

```
┌─────────────┐
│   Customer  │ (Calls via phone)
└──────┬──────┘
       │
       v
┌─────────────────────────────────────────┐
│           VAPI Voice AI                 │
│  (Speech-to-Text, NLP, Text-to-Speech) │
└──────────────┬──────────────────────────┘
               │
               │ HTTPS Webhook POST
               │ (Tool function calls)
               v
┌───────────────────────────────────────────┐
│      Kebabalab Flask Server              │
│      /webhook endpoint                    │
│                                           │
│  ┌─────────────────────────────────┐    │
│  │  15 Tool Functions              │    │
│  │  (checkOpen, quickAddItem, etc.)│    │
│  └─────────────────────────────────┘    │
│                                           │
│  ┌─────────────────────────────────┐    │
│  │  Session Storage                │    │
│  │  (Redis or In-Memory)           │    │
│  └─────────────────────────────────┘    │
│                                           │
│  ┌─────────────────────────────────┐    │
│  │  SQLite Database                │    │
│  │  (Persistent order storage)     │    │
│  └─────────────────────────────────┘    │
└───────────────────────────────────────────┘
               │
               │ SMS (optional)
               v
┌───────────────────────────────────────────┐
│      Twilio SMS Service (Optional)        │
└───────────────────────────────────────────┘
```

---

## 📞 Complete Order Flow (Step-by-Step)

### PHASE 1: CALL INITIATION & GREETING

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Customer Calls                                           │
├─────────────────────────────────────────────────────────────┤
│ • VAPI receives call                                        │
│ • Creates session with call ID & customer phone number      │
│ • Greets customer with AI assistant                         │
│ • Assistant asks: "What can I get for you today?"          │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 2. Check Shop Status                                        │
├─────────────────────────────────────────────────────────────┤
│ TOOL: checkOpen()                                           │
│                                                             │
│ Input: None                                                 │
│                                                             │
│ Process:                                                    │
│ ├─ Get current time in shop timezone (Australia/Melbourne) │
│ ├─ Check against hardcoded hours:                          │
│ │  • Mon-Fri: 11:00 AM - 10:00 PM                         │
│ │  • Sat-Sun: 12:00 PM - 10:00 PM                         │
│ └─ Return status + opening/closing time                    │
│                                                             │
│ Output:                                                     │
│ ├─ If OPEN: "We're open until 10:00 PM"                   │
│ └─ If CLOSED: "We're closed. We open at 11:00 AM"         │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 2: BUILDING THE ORDER

```
┌─────────────────────────────────────────────────────────────┐
│ 3. Customer Orders Items                                    │
├─────────────────────────────────────────────────────────────┤
│ Customer: "Large lamb kebab with no onion, and a small HSP"│
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 4A. Add First Item - Large Lamb Kebab                      │
├─────────────────────────────────────────────────────────────┤
│ TOOL: quickAddItem()                                        │
│                                                             │
│ Input Parameters:                                           │
│ ├─ itemName: "lamb kebab"                                  │
│ ├─ size: "large"                                           │
│ ├─ quantity: 1                                             │
│ ├─ saladsRaw: null (uses defaults)                        │
│ ├─ saucesRaw: "garlic" (default)                          │
│ ├─ excludeIngredients: "onion"                            │
│ └─ extras: null                                            │
│                                                             │
│ Processing Steps:                                           │
│ 1. Parse & normalize item name                             │
│    ├─ Fuzzy match "lamb kebab" → KEB_LAMB                 │
│    └─ Find in menu.json: kebabs category                   │
│                                                             │
│ 2. Get price for size                                      │
│    └─ menu.json: sizes.large = $15.00                     │
│                                                             │
│ 3. Parse exclusions                                        │
│    ├─ Input: "onion"                                       │
│    ├─ Parse with parse_salads()                            │
│    └─ Result: exclude ["onion"] from defaults             │
│                                                             │
│ 4. Build salads list                                       │
│    ├─ Defaults: ["lettuce", "tomato", "onion"]           │
│    ├─ Remove: ["onion"]                                    │
│    └─ Final: ["lettuce", "tomato"]                        │
│                                                             │
│ 5. Build sauces list                                       │
│    └─ Default: ["garlic"]                                  │
│                                                             │
│ 6. Build cart item object                                  │
│    {                                                        │
│      "id": "KEB_LAMB",                                     │
│      "name": "Lamb Kebab",                                 │
│      "category": "kebabs",                                 │
│      "size": "large",                                      │
│      "price": 15.00,                                       │
│      "quantity": 1,                                        │
│      "salads": ["lettuce", "tomato"],                     │
│      "excluded_salads": ["onion"],                        │
│      "sauces": ["garlic"],                                │
│      "extras": [],                                         │
│      "is_combo": false                                     │
│    }                                                        │
│                                                             │
│ 7. Store in session                                        │
│    ├─ Get cart from session_get('cart', [])               │
│    ├─ Append new item                                      │
│    └─ Save with session_set('cart', cart)                 │
│                                                             │
│ Session Storage (Redis or In-Memory):                      │
│ ┌─────────────────────────────────────┐                   │
│ │ Key: session:<phone>:cart           │                   │
│ │ TTL: 1800 seconds (30 minutes)      │                   │
│ │ Value: [cart_item_1, ...]           │                   │
│ └─────────────────────────────────────┘                   │
│                                                             │
│ Output to VAPI:                                            │
│ {                                                           │
│   "ok": true,                                              │
│   "message": "Added large Lamb Kebab ($15.00) to cart",   │
│   "cartSize": 1                                            │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 4B. Add Second Item - Small Chicken HSP                    │
├─────────────────────────────────────────────────────────────┤
│ TOOL: quickAddItem()                                        │
│                                                             │
│ Input:                                                      │
│ ├─ itemName: "chicken hsp"                                 │
│ ├─ size: "small"                                           │
│ └─ quantity: 1                                             │
│                                                             │
│ Processing:                                                 │
│ ├─ Match: HSP_CHKN in menu.json                           │
│ ├─ Price: $14.00 (small)                                   │
│ ├─ HSP defaults: cheese=true, sauces=["garlic", "chilli"]│
│ └─ Add to cart at index [1]                               │
│                                                             │
│ Output:                                                     │
│ "Added small Chicken HSP ($14.00) to cart. Cart has 2 items"│
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 3: CART MODIFICATIONS (Optional)

```
┌─────────────────────────────────────────────────────────────┐
│ 5. Customer Wants to Modify Cart                           │
├─────────────────────────────────────────────────────────────┤
│ Customer: "Actually, can you change the HSP to large?"     │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 6. Get Current Cart State                                  │
├─────────────────────────────────────────────────────────────┤
│ TOOL: getCartState()                                        │
│                                                             │
│ Process:                                                    │
│ ├─ Retrieve cart from session                             │
│ ├─ Format each item with index number                     │
│ └─ Return human-readable list                             │
│                                                             │
│ Output:                                                     │
│ "Your cart has 2 items:                                    │
│  [0] Large Lamb Kebab - $15.00                            │
│      • No onion                                            │
│  [1] Small Chicken HSP - $14.00"                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 7. Edit Cart Item                                          │
├─────────────────────────────────────────────────────────────┤
│ TOOL: editCartItem()                                        │
│                                                             │
│ Input:                                                      │
│ ├─ itemIndex: 1 (the HSP)                                  │
│ └─ modificationsRaw: {"size": "large"}                     │
│                                                             │
│ Processing:                                                 │
│ 1. Validate item index                                     │
│    └─ Check 0 <= index < len(cart)                        │
│                                                             │
│ 2. Get current item                                        │
│    └─ cart[1] = HSP item                                   │
│                                                             │
│ 3. Parse modifications                                     │
│    └─ Extract size change: small → large                  │
│                                                             │
│ 4. Update item properties                                  │
│    ├─ Change size: "large"                                 │
│    ├─ Lookup new price in menu.json                       │
│    │  └─ HSP_CHKN.sizes.large = $18.00                    │
│    └─ Update item.price = 18.00                           │
│                                                             │
│ 5. Handle combo items                                      │
│    ├─ If is_combo=true:                                    │
│    │  ├─ Recalculate base price                           │
│    │  ├─ Recalculate combo additions (+$5 for chips/drink)│
│    │  └─ Update total combo price                         │
│    └─ Else: Just update base price                        │
│                                                             │
│ 6. Save updated cart                                       │
│    └─ session_set('cart', cart)                           │
│                                                             │
│ Output:                                                     │
│ {                                                           │
│   "ok": true,                                              │
│   "message": "Updated item [1]: Changed size to large,    │
│               new price $18.00",                           │
│   "updatedItem": {...}                                     │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 4: MEAL CONVERSION (Optional)

```
┌─────────────────────────────────────────────────────────────┐
│ 8. Convert to Meal/Combo                                   │
├─────────────────────────────────────────────────────────────┤
│ Customer: "Can I make both of those meals?"                │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 9. Convert Items to Meals                                  │
├─────────────────────────────────────────────────────────────┤
│ TOOL: convertItemsToMeals()                                 │
│                                                             │
│ Input:                                                      │
│ ├─ itemIndices: [0, 1] (or null for all)                  │
│ ├─ drinkBrand: "coke"                                      │
│ ├─ chipsSize: "small"                                      │
│ └─ chipsSalt: "chicken"                                    │
│                                                             │
│ Processing:                                                 │
│ 1. If itemIndices is null:                                 │
│    └─ Auto-select all kebabs & HSPs                       │
│                                                             │
│ 2. For each item in itemIndices:                           │
│                                                             │
│    Item [0] - Large Lamb Kebab:                            │
│    ├─ Check: category = "kebabs" ✓                        │
│    ├─ Check: not already combo ✓                          │
│    ├─ Current price: $15.00                                │
│    ├─ Add combo flag: is_combo = true                     │
│    ├─ Add combo price: +$5.00                             │
│    ├─ New total: $20.00                                    │
│    ├─ Add drink: {brand: "coke", type: "375ml can"}      │
│    ├─ Add chips: {size: "small", salt: "chicken"}        │
│    └─ Remove duplicate drinks if exist                    │
│                                                             │
│    Item [1] - Large Chicken HSP:                           │
│    ├─ Check: category = "hsp" ✓                           │
│    ├─ Check: not already combo ✓                          │
│    ├─ Current price: $18.00                                │
│    ├─ Add combo flag: is_combo = true                     │
│    ├─ Add combo price: +$5.00                             │
│    ├─ New total: $23.00                                    │
│    ├─ Add drink: {brand: "coke", type: "375ml can"}      │
│    └─ Add chips: {size: "small", salt: "chicken"}        │
│                                                             │
│ 3. Check for duplicate drinks                              │
│    ├─ Scan cart for standalone drink items                │
│    └─ Remove if combo already includes drink              │
│                                                             │
│ 4. Save updated cart                                       │
│    └─ session_set('cart', updated_cart)                   │
│                                                             │
│ Current Cart State:                                         │
│ [                                                           │
│   {                                                         │
│     "name": "Lamb Kebab",                                  │
│     "size": "large",                                       │
│     "price": 20.00,        // Was 15.00                   │
│     "is_combo": true,      // New flag                    │
│     "combo_drink": {...},  // Added                       │
│     "combo_chips": {...}   // Added                       │
│   },                                                        │
│   {                                                         │
│     "name": "Chicken HSP",                                 │
│     "size": "large",                                       │
│     "price": 23.00,        // Was 18.00                   │
│     "is_combo": true,                                      │
│     "combo_drink": {...},                                  │
│     "combo_chips": {...}                                   │
│   }                                                         │
│ ]                                                           │
│                                                             │
│ Output:                                                     │
│ "Converted 2 items to meals. Added drinks and chips."     │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 5: PRICING & REVIEW

```
┌─────────────────────────────────────────────────────────────┐
│ 10. Calculate Total                                        │
├─────────────────────────────────────────────────────────────┤
│ TOOL: priceCart()                                           │
│                                                             │
│ Input: None (uses current cart from session)               │
│                                                             │
│ Processing:                                                 │
│ 1. Get cart from session                                   │
│    └─ cart = session_get('cart', [])                      │
│                                                             │
│ 2. Calculate total (GST-inclusive)                         │
│    ├─ Item 0: $20.00 × 1 = $20.00                         │
│    ├─ Item 1: $23.00 × 1 = $23.00                         │
│    └─ Total: $43.00                                        │
│                                                             │
│ 3. Calculate GST component (NEW FEATURE)                   │
│    ├─ Formula: GST = Total × (0.10 / 1.10)                │
│    ├─ GST = $43.00 × 0.0909 = $3.91                       │
│    └─ Subtotal (ex GST) = $43.00 - $3.91 = $39.09        │
│                                                             │
│ 4. Store totals in session                                 │
│    ├─ session_set('cart_priced', True)                    │
│    ├─ session_set('last_subtotal', 39.09)                 │
│    ├─ session_set('last_gst', 3.91)                       │
│    ├─ session_set('last_total', 43.00)                    │
│    └─ session_set('last_totals', {...})                   │
│                                                             │
│ Output:                                                     │
│ {                                                           │
│   "ok": true,                                              │
│   "subtotal": 39.09,    // NEW: Ex-GST amount             │
│   "gst": 3.91,          // NEW: GST component             │
│   "total": 43.00,       // Total (GST-inclusive)          │
│   "itemCount": 2,                                          │
│   "message": "Total: $43.00 (inc. $3.91 GST)"            │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 11. Get Order Summary                                      │
├─────────────────────────────────────────────────────────────┤
│ TOOL: getOrderSummary()                                     │
│                                                             │
│ Purpose: Generate human-readable summary for speech        │
│                                                             │
│ Processing:                                                 │
│ 1. Retrieve cart and totals                                │
│ 2. Format each item for natural speech:                    │
│    ├─ "1 Large Lamb Kebab meal with lettuce, tomato,     │
│    │   no onion, and garlic sauce, with Coke and chips"   │
│    └─ "1 Large Chicken HSP meal with cheese, garlic and   │
│        chilli sauce, with Coke and chips"                  │
│                                                             │
│ 3. Format total                                            │
│    └─ "Your total is $43.00"                              │
│                                                             │
│ Output (for VAPI to speak):                                │
│ "Here's your order:                                        │
│  • Large Lamb Kebab meal - $20                            │
│  • Large Chicken HSP meal - $23                           │
│  Your total is $43.00"                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 6: PICKUP TIME

```
┌─────────────────────────────────────────────────────────────┐
│ 12. Set Pickup Time                                        │
├─────────────────────────────────────────────────────────────┤
│ Customer: "I'd like it ready in 20 minutes"               │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 13A. Option 1: Customer Specifies Time                     │
├─────────────────────────────────────────────────────────────┤
│ TOOL: setPickupTime()                                       │
│                                                             │
│ Input:                                                      │
│ ├─ minutesFromNow: 20                                      │
│ └─ OR specificTime: "5:30 PM"                             │
│                                                             │
│ Processing:                                                 │
│ 1. Get current time in shop timezone                       │
│    └─ now = datetime.now(SHOP_TIMEZONE)                   │
│    └─ now = 2025-10-29 17:10:00 AEDT                      │
│                                                             │
│ 2. Calculate ready time                                    │
│    ├─ If minutesFromNow provided:                         │
│    │  └─ ready = now + timedelta(minutes=20)              │
│    │  └─ ready = 17:30:00                                 │
│    └─ If specificTime:                                     │
│       └─ Parse "5:30 PM" → 17:30:00                       │
│                                                             │
│ 3. Validate time                                           │
│    ├─ Must be in future                                    │
│    ├─ Must be during shop hours                           │
│    └─ Must be reasonable (< 4 hours from now)             │
│                                                             │
│ 4. Format for storage and speech                           │
│    ├─ ISO: "2025-10-29T17:30:00+11:00"                    │
│    ├─ Formatted: "5:30 PM"                                 │
│    └─ Speech: "five thirty PM"                            │
│                                                             │
│ 5. Store in session                                        │
│    ├─ session_set('pickup_confirmed', True)               │
│    ├─ session_set('ready_at', iso_time)                   │
│    ├─ session_set('ready_at_formatted', "5:30 PM")       │
│    └─ session_set('ready_at_speech', "five thirty PM")   │
│                                                             │
│ Output:                                                     │
│ "Your order will be ready at 5:30 PM"                     │
└─────────────────────────────────────────────────────────────┘
                          │
                          OR
                          v
┌─────────────────────────────────────────────────────────────┐
│ 13B. Option 2: Estimate Ready Time                         │
├─────────────────────────────────────────────────────────────┤
│ TOOL: estimateReadyTime()                                   │
│                                                             │
│ Purpose: Auto-calculate based on current time & load       │
│                                                             │
│ Input:                                                      │
│ └─ addMinutes: 0 (optional adjustment)                     │
│                                                             │
│ Processing:                                                 │
│ 1. Get base preparation time                               │
│    └─ Default: 15 minutes (normal)                        │
│    └─ Busy: 25 minutes (peak hours)                       │
│                                                             │
│ 2. Check if currently busy                                 │
│    ├─ Peak hours: 12-2 PM, 6-8 PM                         │
│    └─ Use longer estimate if busy                         │
│                                                             │
│ 3. Add customer adjustment                                 │
│    └─ estimate += addMinutes                              │
│                                                             │
│ 4. Calculate ready time                                    │
│    └─ ready = now + estimate                              │
│                                                             │
│ 5. Store same as setPickupTime                            │
│                                                             │
│ Output:                                                     │
│ "Your order will be ready in approximately 15 minutes"    │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 7: CUSTOMER INFO & ORDER CREATION

```
┌─────────────────────────────────────────────────────────────┐
│ 14. Collect Customer Information                           │
├─────────────────────────────────────────────────────────────┤
│ VAPI AI: "Can I get your name for the order?"             │
│ Customer: "John Smith"                                     │
│                                                             │
│ VAPI AI: "And a phone number?"                            │
│ Customer: "0412 345 678"                                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          v
┌─────────────────────────────────────────────────────────────┐
│ 15. Create Order                                           │
├─────────────────────────────────────────────────────────────┤
│ TOOL: createOrder()                                         │
│                                                             │
│ Input:                                                      │
│ ├─ customerName: "John Smith"                              │
│ ├─ customerPhone: "0412345678"                            │
│ ├─ notes: ""                                               │
│ └─ sendSMS: true                                           │
│                                                             │
│ Validation Steps:                                           │
│ 1. Validate customer name                                  │
│    ├─ Check length: 2-100 characters ✓                    │
│    ├─ Check format: letters, spaces, hyphens ✓            │
│    ├─ Sanitize for SMS: remove control chars ✓            │
│    └─ Result: "John Smith"                                 │
│                                                             │
│ 2. Validate phone number                                   │
│    ├─ Input: "0412345678"                                  │
│    ├─ Remove spaces/dashes: "0412345678"                  │
│    ├─ Check format: Australian mobile ✓                   │
│    ├─ Normalize: "+61412345678"                           │
│    └─ Result: "+61412345678"                              │
│                                                             │
│ 3. Validate cart exists                                    │
│    ├─ cart = session_get('cart', [])                      │
│    ├─ Check not empty ✓                                    │
│    └─ Check priced ✓                                       │
│                                                             │
│ 4. Validate pickup time confirmed                          │
│    ├─ Check: session_get('pickup_confirmed') = True ✓     │
│    └─ Check: ready_at exists ✓                            │
│                                                             │
│ Database Operations:                                        │
│ 1. Generate order number                                   │
│    ├─ Format: YYYYMMDD-NNN                                 │
│    ├─ Query: COUNT orders today                           │
│    ├─ Count: 42                                            │
│    └─ Result: "20251029-043"                              │
│                                                             │
│ 2. Insert order into database                              │
│    ┌───────────────────────────────────────┐              │
│    │ SQLite: orders table                  │              │
│    ├───────────────────────────────────────┤              │
│    │ INSERT INTO orders (                  │              │
│    │   order_number: "20251029-043",       │              │
│    │   customer_name: "John Smith",        │              │
│    │   customer_phone: "+61412345678",     │              │
│    │   cart_json: "[{...}, {...}]",        │              │
│    │   subtotal: 39.09,                    │              │
│    │   gst: 3.91,                          │              │
│    │   total: 43.00,                       │              │
│    │   ready_at: "2025-10-29T17:30:00+11", │              │
│    │   notes: "",                          │              │
│    │   status: "pending",                  │              │
│    │   created_at: CURRENT_TIMESTAMP       │              │
│    │ )                                     │              │
│    └───────────────────────────────────────┘              │
│                                                             │
│ 3. Commit transaction                                      │
│    └─ Database persists order ✓                           │
│                                                             │
│ SMS Notification (if sendSMS=true):                        │
│ 1. Build SMS message                                       │
│    ┌────────────────────────────────────┐                 │
│    │ Kebabalab Order #043               │                 │
│    │                                    │                 │
│    │ John Smith                         │                 │
│    │ Ready: 5:30 PM                     │                 │
│    │                                    │                 │
│    │ Items:                             │                 │
│    │ • Large Lamb Kebab meal            │                 │
│    │ • Large Chicken HSP meal           │                 │
│    │                                    │                 │
│    │ Total: $43.00                      │                 │
│    │                                    │                 │
│    │ Kebabalab - Melbourne              │                 │
│    └────────────────────────────────────┘                 │
│                                                             │
│ 2. Send via Twilio (if configured)                        │
│    ├─ To: Shop phone number                               │
│    ├─ From: Twilio number                                 │
│    └─ Body: Order confirmation                            │
│                                                             │
│ 3. Clear session                                           │
│    ├─ session_clear() removes all session data            │
│    └─ Customer can start new order                        │
│                                                             │
│ Output:                                                     │
│ {                                                           │
│   "ok": true,                                              │
│   "orderNumber": "20251029-043",                          │
│   "displayOrder": "#043",                                  │
│   "total": 43.00,                                          │
│   "readyAt": "5:30 PM",                                    │
│   "message": "Order #043 confirmed! Ready at 5:30 PM.    │
│               Total: $43.00. See you soon!"               │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

### PHASE 8: CALL COMPLETION

```
┌─────────────────────────────────────────────────────────────┐
│ 16. End Call                                               │
├─────────────────────────────────────────────────────────────┤
│ TOOL: endCall()                                             │
│                                                             │
│ Purpose: Gracefully end conversation                        │
│                                                             │
│ Input:                                                      │
│ └─ reason: "order_complete" (or "customer_request")        │
│                                                             │
│ Processing:                                                 │
│ 1. Generate closing message                                │
│    └─ "Thank you for your order! See you at 5:30 PM."    │
│                                                             │
│ 2. Log call completion                                     │
│    └─ logger.info("Call ended: order_complete")           │
│                                                             │
│ 3. Return signal to VAPI                                   │
│    └─ VAPI ends call gracefully                           │
│                                                             │
│ Output:                                                     │
│ {                                                           │
│   "ok": true,                                              │
│   "endCall": true,                                         │
│   "message": "Thank you for ordering from Kebabalab!"     │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Session Management Flow

### Redis Session Storage (Production)

```
┌──────────────────────────────────────────────────────┐
│                 Redis Server                         │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Key: session:+61412345678:cart                     │
│  TTL: 1800 seconds (30 minutes)                     │
│  Value: [{item1}, {item2}]                          │
│                                                      │
│  Key: session:+61412345678:cart_priced              │
│  TTL: 1800 seconds                                   │
│  Value: "true"                                       │
│                                                      │
│  Key: session:+61412345678:last_total               │
│  TTL: 1800 seconds                                   │
│  Value: "43.00"                                      │
│                                                      │
│  Key: session:+61412345678:ready_at                 │
│  TTL: 1800 seconds                                   │
│  Value: "2025-10-29T17:30:00+11:00"                 │
│                                                      │
│  • Automatic expiration via TTL                     │
│  • Persistent across server restarts                │
│  • Shared across multiple server instances          │
│  • Production-ready                                  │
└──────────────────────────────────────────────────────┘
```

### In-Memory Session Storage (Fallback)

```
┌──────────────────────────────────────────────────────┐
│              Python Process Memory                   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  SESSIONS = {                                        │
│    "+61412345678": {                                 │
│      "_meta": {                                      │
│        "created_at": datetime(...),                  │
│        "last_access": datetime(...)                  │
│      },                                              │
│      "cart": [{item1}, {item2}],                    │
│      "cart_priced": True,                           │
│      "last_total": 43.00,                           │
│      "ready_at": "2025-10-29T17:30:00+11:00"        │
│    }                                                 │
│  }                                                   │
│                                                      │
│  • Manual cleanup every 5 minutes                   │
│  • Lost on server restart                           │
│  • Single server only                               │
│  • Development/testing only                         │
└──────────────────────────────────────────────────────┘
```

---

## 🛠️ Complete Tool Reference

### All 15 Available Tools:

| # | Tool Name | Purpose | Key Parameters |
|---|-----------|---------|----------------|
| 1 | `checkOpen` | Check if shop is open | None |
| 2 | `getCallerSmartContext` | Get caller history | None |
| 3 | `quickAddItem` | Add item to cart | itemName, size, quantity, exclusions, extras |
| 4 | `addMultipleItemsToCart` | Batch add items | items[] |
| 5 | `getCartState` | View current cart | None |
| 6 | `removeCartItem` | Remove item | itemIndex |
| 7 | `editCartItem` | Modify item | itemIndex, modifications |
| 8 | `priceCart` | Calculate totals | None |
| 9 | `convertItemsToMeals` | Add drink+chips | itemIndices[], drinkBrand, chipsSize |
| 10 | `getOrderSummary` | Format for speech | None |
| 11 | `setPickupTime` | Set specific time | minutesFromNow or specificTime |
| 12 | `estimateReadyTime` | Auto-calculate time | addMinutes |
| 13 | `createOrder` | Finalize & save order | customerName, customerPhone, notes, sendSMS |
| 14 | `sendMenuLink` | Text menu URL | None |
| 15 | `repeatLastOrder` | Reorder previous | None |
| 16 | `sendReceipt` | Text receipt | None |
| 17 | `endCall` | End conversation | reason |

---

## 🔍 Data Flow Through System

```
Call Start
    │
    ├─> VAPI recognizes speech
    │   └─> Converts to text: "Large lamb kebab with no onion"
    │
    ├─> VAPI NLP determines intent
    │   └─> Decides to call: quickAddItem()
    │
    ├─> VAPI sends webhook POST to /webhook
    │   POST /webhook
    │   {
    │     "message": {
    │       "toolCalls": [{
    │         "function": {
    │           "name": "quickAddItem",
    │           "arguments": {
    │             "itemName": "lamb kebab",
    │             "size": "large",
    │             "excludeIngredients": "onion"
    │           }
    │         }
    │       }]
    │     }
    │   }
    │
    ├─> Flask Server receives request
    │   └─> webhook() function processes
    │       └─> Calls tool_quick_add_item()
    │
    ├─> Tool processes request
    │   ├─> Fuzzy match "lamb kebab" → KEB_LAMB
    │   ├─> Lookup price: menu.json → $15.00
    │   ├─> Parse exclusions: ["onion"]
    │   ├─> Build cart item object
    │   └─> Store in session: session_set('cart', [item])
    │
    ├─> Redis/Memory stores data
    │   └─> Key: session:+61412345678:cart
    │       Value: [{id: "KEB_LAMB", ...}]
    │       TTL: 1800 seconds
    │
    ├─> Return result to VAPI
    │   Response: {
    │     "results": [{
    │       "toolCallId": "...",
    │       "result": {
    │         "ok": true,
    │         "message": "Added large Lamb Kebab ($15.00)"
    │       }
    │     }]
    │   }
    │
    └─> VAPI speaks result
        └─> Text-to-Speech: "I've added a large lamb kebab
            with no onion to your order, that's $15."
```

---

## 🚨 Error Handling Flow

```
Error occurs in tool
    │
    ├─> Exception caught by try/catch
    │
    ├─> Logged internally
    │   └─> logger.error(f"Error in quickAddItem: {e}", exc_info=True)
    │       └─> Writes to: logs/kebabalab_simplified.log
    │           └─> Full stack trace with details
    │
    ├─> Return error to VAPI
    │   └─> {"ok": false, "error": str(e)}
    │       └─> NOTE: Currently exposes full error message
    │           └─> SECURITY CONCERN: Shows internal details
    │
    └─> VAPI speaks error
        └─> "I'm sorry, there was an error: [error message]"
```

---

## 📊 Database Schema

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,      -- "20251029-043"
    customer_name TEXT NOT NULL,             -- "John Smith"
    customer_phone TEXT NOT NULL,            -- "+61412345678"
    cart_json TEXT NOT NULL,                 -- JSON array of items
    subtotal REAL NOT NULL,                  -- 39.09 (ex-GST)
    gst REAL NOT NULL,                       -- 3.91
    total REAL NOT NULL,                     -- 43.00 (GST-inclusive)
    ready_at TEXT,                           -- "2025-10-29T17:30:00+11:00"
    notes TEXT,                              -- Customer notes
    status TEXT DEFAULT 'pending',           -- Order status
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_order_number ON orders(order_number);
CREATE INDEX idx_customer_phone ON orders(customer_phone);
CREATE INDEX idx_status ON orders(status);
CREATE INDEX idx_created_at ON orders(created_at);
```

---

## ⏱️ Timing & Performance

```
Typical Order Flow Timing:
┌────────────────────────────────────────────┐
│ Action                    │ Time (approx.) │
├───────────────────────────┼────────────────┤
│ Call initiation           │ 1-2 seconds    │
│ Shop hours check          │ 50-100ms       │
│ Add item (each)           │ 100-200ms      │
│ Menu lookup + fuzzy match │ 50-150ms       │
│ Session write (Redis)     │ 10-50ms        │
│ Session write (In-memory) │ <1ms           │
│ Price calculation         │ 20-50ms        │
│ Database order insert     │ 50-200ms       │
│ SMS send (Twilio)         │ 500-2000ms     │
│ Complete order creation   │ 1-3 seconds    │
│ Total call duration       │ 2-5 minutes    │
└────────────────────────────────────────────┘
```

---

## 🎯 Critical Flow Points (Where Issues May Occur)

### 1. **Fuzzy Matching** (`parse_item_name()`)
- If rapidfuzz not installed → Falls back to exact string matching
- May fail to match typos or variations
- **Risk:** Customer says "lam kebab" → No match found

### 2. **Session Persistence**
- Redis not available → Falls back to in-memory
- Server restart → All sessions lost
- **Risk:** Customer disconnects mid-order → Order lost

### 3. **Menu Price Lookup**
- Item must exist in menu.json with correct size
- Combo pricing adds $5.00 fixed
- **Risk:** Invalid size requested → Error returned

### 4. **GST Calculation** (NEWLY FIXED)
- Prices in menu.json are GST-inclusive
- GST component calculated: Total × (0.10/1.10)
- **Was showing:** $0.00 GST (BUG)
- **Now shows:** Correct GST component

### 5. **Pickup Time Validation**
- Must be in future
- Must be during shop hours
- Must be confirmed before order creation
- **Risk:** Time not set → Order creation blocked

### 6. **Order Number Generation**
- Format: YYYYMMDD-NNN
- Sequential counter per day
- **Risk:** Race condition if two orders at exact same time
- **Mitigation:** Database UNIQUE constraint

### 7. **SMS Delivery**
- Requires Twilio credentials
- May fail silently if not configured
- **Risk:** Shop doesn't receive notification

---

## 🔐 Security Considerations

### Current Issues:
1. ❌ **Error messages expose system details**
   - Returns: `str(e)` to VAPI
   - Shows: Database paths, file system structure, stack traces

2. ❌ **No rate limiting**
   - Unlimited webhook calls per minute
   - Vulnerable to abuse

3. ❌ **CORS allows all origins** (for testing)
   - CORS(app) → Allows *
   - Production should restrict to VAPI domains

4. ❌ **No request signature verification**
   - Any POST to /webhook accepted
   - Should verify VAPI webhook signature

5. ✅ **Credentials in .env** (GOOD)
   - Not committed to git
   - Loaded via python-dotenv

6. ✅ **SMS sanitization** (GOOD)
   - Removes control characters
   - Limited to 500 chars

---

## 📈 Scalability Considerations

### Current Setup (Single Server):
```
Concurrent Sessions: 1000 (hardcoded limit for in-memory)
Session Storage: In-memory (not shared)
Database: SQLite (single file, write locks)
Webhooks: Synchronous processing
```

### For Production Scale:
```
✓ Use Redis (shared session storage)
✓ Use PostgreSQL (better concurrency)
✓ Add load balancer
✓ Add webhook queue (Celery/RQ)
✓ Add monitoring (Sentry, DataDog)
✓ Add rate limiting (Flask-Limiter)
```

---

## 🎬 Example Complete Order

```
Timeline of actual order:

00:00 - Customer calls Kebabalab
00:05 - checkOpen() → "We're open until 10 PM"
00:15 - quickAddItem("lamb kebab", "large", exclude="onion")
00:20 - quickAddItem("chicken hsp", "small")
00:30 - getCartState() → Shows 2 items
00:35 - editCartItem(1, {size: "large"}) → HSP now large
00:45 - convertItemsToMeals([0,1]) → Both become combos
01:00 - priceCart() → Total: $43.00
01:05 - getOrderSummary() → Reads items aloud
01:20 - estimateReadyTime() → "Ready in 15 minutes"
01:35 - createOrder("John Smith", "0412345678")
01:40 - Database INSERT → Order #043
01:45 - SMS sent via Twilio
01:50 - Session cleared
01:55 - endCall("order_complete")
02:00 - Call ends
```

---

## 🎨 Visual State Machine

```
   [START]
      │
      v
  ┌────────┐
  │ IDLE   │ (No cart exists)
  └───┬────┘
      │ quickAddItem()
      v
  ┌────────┐
  │BUILDING│ (Cart has items, not priced)
  └───┬────┘
      │ priceCart()
      v
  ┌────────┐
  │ PRICED │ (Totals calculated)
  └───┬────┘
      │ setPickupTime()
      v
  ┌────────┐
  │  READY │ (Ready for order creation)
  └───┬────┘
      │ createOrder()
      v
  ┌─────────┐
  │COMPLETED│ (Order in database)
  └───┬─────┘
      │ session_clear()
      v
   [END]
```

---

## Summary

This diagram shows:
- ✅ All 17 tools and their purposes
- ✅ Complete order flow from call to completion
- ✅ Session management (Redis + fallback)
- ✅ GST calculation (NOW FIXED)
- ✅ Database storage structure
- ✅ Error handling patterns
- ✅ Timing and performance metrics
- ⚠️ Security concerns identified
- ⚠️ Scalability limitations noted
- ⚠️ Critical points where issues may occur

**Key Takeaways:**
1. System is functional end-to-end
2. Recent bugs (no cheese, HSP pricing) are fixed
3. GST now calculates correctly from inclusive prices
4. Redis session storage implemented for production
5. Some security hardening still needed
6. Error messages too detailed (security risk)
7. CORS currently wide open (testing mode)


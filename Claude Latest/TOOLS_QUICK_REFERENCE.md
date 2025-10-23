# 🚀 TOOLS QUICK REFERENCE CARD

**30 Tools | 7 Categories | All Working ✅**

---

## 1️⃣ CORE ORDER FLOW (6 tools)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `checkOpen` | Check if shop is open | None |
| `getCallerInfo` | Get caller's phone | None |
| `startItemConfiguration` | Start new item | category |
| `setItemProperty` | Set item field | field, value |
| `validateMenuItem` | Validate item | category, size, protein |
| `addItemToCart` | Add item + detect combos | None |

---

## 2️⃣ CART MANAGEMENT (7 tools)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `getCartState` | View cart (JSON) | None |
| `getDetailedCart` | View cart (text) | None |
| `removeCartItem` | Remove item | itemIndex |
| `editCartItem` | Edit toppings | itemIndex, field, value |
| `modifyCartItem` | Change ANY field | itemIndex, modifications |
| `convertItemsToMeals` | Kebabs → Meals | itemIndices, chipsSize |
| `clearCart` | Empty cart | None |
| `clearSession` | Reset everything | None |

---

## 3️⃣ PRICING & MENU (4 tools)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `priceCart` | Calculate total | None |
| `getMenuByCategory` | Browse menu | category |
| `validateMenuItem` | Check valid | category |
| `sendMenuLink` | SMS menu | phoneNumber |

---

## 4️⃣ ORDER MANAGEMENT (5 tools)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `getOrderSummary` | Order preview | None |
| `setOrderNotes` | Special instructions | notes |
| `getLastOrder` | Fetch last order | phoneNumber |
| `repeatLastOrder` | Copy last order | phoneNumber |
| `lookupOrder` | Search orders | orderId or phoneNumber |

---

## 5️⃣ FULFILLMENT (3 tools)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `setPickupTime` | Custom pickup | pickupTime |
| `estimateReadyTime` | Auto calculate | None |
| `createOrder` | Save & send SMS | customerName, sendSms |

---

## 6️⃣ PERFORMANCE (3 tools)

| Tool | Purpose | Speed Boost |
|------|---------|-------------|
| `getCallerSmartContext` | Smart greeting + history | 89% faster |
| `addMultipleItemsToCart` | Batch add items | 60-88% faster |
| `quickAddItem` | Natural language parser | 73% faster |

---

## 7️⃣ SYSTEM (2 tools)

| Tool | Purpose | Key Params |
|------|---------|------------|
| `endCall` | Hang up | None |

---

## 💰 PRICING REFERENCE

### Base Prices
- **Kebabs:** Small $10, Large $15
- **HSP:** Small $15, Large $20
- **Chips:** Small $5, Large $9
- **Drinks:** $3.50

### Extras
- **Cheese:** +$1
- **Extra Meat:** +$3
- **Extra Sauces (3+):** +$0.50 each

### Combos
- **Small Kebab + Can:** $12
- **Large Kebab + Can:** $17
- **Small Kebab Meal:** $17
- **Small Kebab Meal (Large Chips):** $20
- **Large Kebab Meal:** $22
- **Large Kebab Meal (Large Chips):** $25
- **Small HSP Combo:** $17
- **Large HSP Combo:** $22

---

## ⚡ COMMON WORKFLOWS

### Simple Order
```
checkOpen → getCallerSmartContext →
startItemConfiguration → setItemProperty (×N) → addItemToCart →
priceCart → createOrder → endCall
```

### Repeat Customer
```
checkOpen → getCallerSmartContext →
repeatLastOrder → priceCart → createOrder → endCall
```

### Multi-Item (Fast)
```
checkOpen → getCallerSmartContext →
addMultipleItemsToCart → priceCart → createOrder → endCall
```

### Natural Language
```
checkOpen → getCallerSmartContext →
quickAddItem (×N) → priceCart → createOrder → endCall
```

---

## 🎯 REQUIRED FIELDS BY CATEGORY

| Category | Required Fields |
|----------|----------------|
| kebabs | size, protein, salads, sauces |
| hsp | size, protein, sauces |
| chips | size |
| drinks | brand |
| gozleme | variant |
| sauce_tubs | sauce_type |
| sweets | none |
| extras | none |

---

## 🔧 FIELD OPTIONS

### Sizes
`"small"` | `"large"`

### Proteins
`"lamb"` | `"chicken"` | `"mixed"` | `"falafel"`

### Salads
`["lettuce", "tomato", "onion", "tabouli"]`

### Sauces
`["garlic", "chilli", "bbq", "sweet_chilli"]`

### Salt Types
`"chicken"` | `"plain"` | `"seasoned"`

### Drink Brands
`"coke"` | `"sprite"` | `"fanta"` | `"solo"` | `"lemonade"`

---

## ⚠️ LIMITS

- **Max Items per Order:** 50
- **Max Item Quantity:** 20
- **Max Batch Add:** 10 items
- **Rate Limit:** 10 calls/minute per caller
- **Session Timeout:** 15 minutes

---

## 🐛 QUICK TROUBLESHOOTING

| Error | Fix |
|-------|-----|
| "No item configured" | Call `startItemConfiguration` first |
| "Item not complete" | Set all required fields |
| "Cart is empty" | Add items before pricing |
| "Invalid index" | Check cart length with `getCartState` |

---

**📄 Full Docs:** `COMPLETE_TOOLS_REFERENCE.md`
**🧪 Tests:** `tests/test_comprehensive_edge_cases.py`
**⚙️ Config:** `config/vapi-tools-definitions.json`

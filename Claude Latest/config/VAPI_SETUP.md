# VAPI Setup Guide - Kebabalab

## Quick Start

### 1. System Prompt
Upload `system-prompt-simplified.md` to your VAPI assistant configuration.

### 2. Tools Configuration
Upload `vapi-tools-simplified.json` to VAPI. Update `YOUR_WEBHOOK_URL` with your actual webhook endpoint.

### 3. Webhook URL
Set your webhook URL to: `https://your-domain.com/webhook`

## Configuration Steps

### Step 1: Deploy Server

```bash
# Install dependencies
cd "Claude Latest"
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run server
python -m kebabalab.server
```

Server will be available at `http://localhost:5000`

### Step 2: Configure VAPI

1. **Create Assistant**
   - Go to VAPI dashboard
   - Create new assistant
   - Name: "Kebabalab Phone Assistant"

2. **Upload System Prompt**
   - Copy contents of `config/system-prompt-simplified.md`
   - Paste into VAPI assistant system prompt field

3. **Configure Tools**
   - Upload `config/vapi-tools-simplified.json`
   - Replace `YOUR_WEBHOOK_URL` with your actual webhook
   - All 18 tools should be registered

4. **Test Connection**
   - Use VAPI test call feature
   - Verify webhook responds correctly

### Step 3: Configure Phone Number

1. Purchase phone number through VAPI
2. Assign number to your Kebabalab assistant
3. Configure business hours (11am-11pm most days)

## Tools Overview (18 Total)

### Core Tools
1. **checkOpen** - Verify shop is open
2. **getCallerSmartContext** - Get caller info and history
3. **quickAddItem** - Add items via natural language (PRIMARY TOOL)
4. **addMultipleItemsToCart** - Batch add items
5. **getCartState** - Review current order
6. **removeCartItem** - Remove specific items
7. **clearCart** - Clear entire cart
8. **editCartItem** - Modify existing items

### Order Management
9. **priceCart** - Calculate total
10. **convertItemsToMeals** - Upgrade to combo meals
11. **getOrderSummary** - Get formatted order summary
12. **setPickupTime** - Set specific pickup time
13. **estimateReadyTime** - Calculate preparation time
14. **createOrder** - Finalize and save order

### Customer Service
15. **sendMenuLink** - SMS menu link
16. **sendReceipt** - SMS receipt
17. **repeatLastOrder** - Reorder previous
18. **endCall** - End call gracefully

## Menu-Specific Notes

### Kebabs ($10 small / $15 large)
- Proteins: Lamb, Chicken, Mixed, Falafel
- Salads: lettuce, tomato, onion, pickles, olives
- Sauces: garlic, chilli, BBQ, tomato, sweet chilli, mayo, hummus

**Example Orders:**
```
"large lamb kebab"
"small chicken kebab no onion"
"large mixed kebab with bbq sauce"
```

### HSP - Halal Snack Pack ($15 small / $20 large)
- Cheese INCLUDED (don't charge extra)
- Same proteins as kebabs
- HSP Combos: Small $17, Large $22 (includes can)

**Example Orders:**
```
"large lamb hsp"
"small chicken hsp no cheese"
"large mixed hsp combo with coke"
```

### Combos/Meals
- Kebab + Small Chips + Can: Small $17, Large $22
- Kebab + Large Chips + Can: Large $25
- HSP + Can: Small $17, Large $22

**Always suggest combos when customer orders items separately!**

### Other Items
- Chips: $5 small, $9 large (chicken salt default)
- Drinks: $3.50 (Coke, Sprite, Fanta, Water, etc.)
- Gözleme: $15 (Lamb, Chicken, Veg, Vegan)
- Baklava: $3.00 each, $10 for 4-pack

## Testing Checklist

- [ ] Server responds to `/health` endpoint
- [ ] All 18 tools registered in VAPI
- [ ] System prompt uploaded
- [ ] Test call connects successfully
- [ ] quickAddItem works for kebabs
- [ ] quickAddItem works for HSPs
- [ ] convertItemsToMeals works
- [ ] Pricing calculates correctly
- [ ] Orders save to database
- [ ] SMS notifications work (if configured)

## Common Issues

### Issue: "Tool not found"
**Solution:** Check tool names in vapi-tools-simplified.json match server.py TOOLS dict

### Issue: "Cheese charged on HSP"
**Solution:** Cheese is INCLUDED in HSPs - pricing logic handles this automatically

### Issue: "Combo pricing wrong"
**Solution:** Use convertItemsToMeals tool to upgrade to meal deals

## Production Deployment

### Using Gunicorn (Recommended)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 kebabalab.server:app
```

### Using HTTPS (Required for VAPI)
Use nginx or similar as reverse proxy with SSL certificate.

### Environment Variables
```bash
SHOP_NAME=Kebabalab
SHOP_ADDRESS=1/99 Carlisle St, St Kilda VIC 3182
SHOP_TIMEZONE=Australia/Melbourne
SHOP_ORDER_TO=+61395345588  # Update with real number
MENU_LINK_URL=https://kebabalab.com.au/menu
```

## Support

For issues:
1. Check logs: `logs/kebabalab_simplified.log`
2. Run tests: `python test_comprehensive_system.py`
3. Verify menu: `python -c "from kebabalab.server import load_menu; load_menu()"`

## Key Features

- **Smart NLP**: quickAddItem handles typos and variations
- **Auto-combos**: System suggests meal deals automatically
- **Order History**: Returning customers can reorder
- **GST Included**: All prices are tax-inclusive
- **Session Management**: Redis (production) or in-memory (dev)

## VAPI-Specific Settings

**Recommended VAPI Configuration:**
- Voice: Natural, friendly Australian accent
- Speed: Normal (not too fast for phone orders)
- Interruption Handling: Allow customer to interrupt
- Background Noise: Medium tolerance
- Silence Timeout: 3-4 seconds
- Model: gpt-4 (for best NLP)

## Testing Example Call Flow

1. **Call starts** → getCallerSmartContext
2. **Customer**: "I want a large lamb kebab"
3. **Assistant**: quickAddItem("large lamb kebab")
4. **Assistant**: "What salads would you like?"
5. **Customer**: "Lettuce, tomato, no onion"
6. **Assistant**: editCartItem(0, {salads: ['lettuce', 'tomato']})
7. **Assistant**: "And sauces?"
8. **Customer**: "Garlic and chilli"
9. **Assistant**: editCartItem(0, {sauces: ['garlic', 'chilli']})
10. **Assistant**: priceCart()
11. **Assistant**: "That'll be $15.00. Anything else?"
12. **Customer**: "No, that's it"
13. **Assistant**: estimateReadyTime()
14. **Assistant**: createOrder(name, phone, time)
15. **Assistant**: "Order #123 confirmed, ready in 15 minutes!"

All 18 tools are compatible and production-ready! 🚀

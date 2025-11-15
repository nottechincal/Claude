# VAPI Setup Guide - Stuffed Lamb

## Quick Start

### 1. System Prompt
Upload `system-prompt.md` to your VAPI assistant configuration.

### 2. Tools Configuration
Upload `vapi-tools.json` to VAPI. Update `YOUR_WEBHOOK_URL` with your actual webhook endpoint.

### 3. Webhook URL
Set your webhook URL to: `https://your-domain.com/webhook`

## Configuration Steps

### Step 1: Deploy Server

```bash
# Install dependencies
cd stuffed-lamb
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run server
python -m stuffed_lamb.server
```

Server will be available at `http://localhost:5000`

### Step 2: Configure VAPI

1. **Create Assistant**
   - Go to VAPI dashboard
   - Create new assistant
   - Name: "Stuffed Lamb Phone Assistant"

2. **Upload System Prompt**
   - Copy contents of `config/system-prompt.md`
   - Paste into VAPI assistant system prompt field

3. **Configure Tools**
   - Upload `config/vapi-tools.json`
   - Replace `YOUR_WEBHOOK_URL` with your actual webhook
   - All 18 tools should be registered

4. **Test Connection**
   - Use VAPI test call feature
   - Verify webhook responds correctly

### Step 3: Configure Phone Number

1. Purchase phone number through VAPI
2. Assign number to your Stuffed Lamb assistant
3. Configure business hours (closed Mon-Tue)

## Tools Overview (18 Total)

### Core Tools
1. **checkOpen** - Verify restaurant is open
2. **getCallerSmartContext** - Get caller info and history
3. **quickAddItem** - Add items via natural language
4. **addMultipleItemsToCart** - Batch add items
5. **getCartState** - Review current order
6. **removeCartItem** - Remove specific items
7. **clearCart** - Clear entire cart
8. **editCartItem** - Modify existing items

### Order Management
9. **priceCart** - Calculate total
10. **convertItemsToMeals** - Not used (Stuffed Lamb has no combos)
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

### Mandi Dishes (Lamb $28, Chicken $23)
- Add-ons: Nuts (+$2.00), Sultanas (+$2.00)
- Extras: Green Chillis, Potato, Tzatziki, Chilli Sauce (+$1.00 each)
- Extra Rice on Plate (+$5.00)

**Example Orders:**
```
"lamb mandi with nuts"
"chicken mandi add nuts and sultanas"
"lamb mandi extra rice on plate"
```

### Mansaf ($33.00)
- Extras: Extra Jameed (+$8.40), Extra Rice (+$8.40)

**Example Orders:**
```
"mansaf"
"mansaf with extra jameed"
"mansaf extra rice"
```

### Drinks & Sides
```
"soup of the day"
"coke"
"2 sprites"
"water"
```

## Testing Checklist

- [ ] Server responds to `/health` endpoint
- [ ] All 18 tools registered in VAPI
- [ ] System prompt uploaded
- [ ] Test call connects successfully
- [ ] quickAddItem works for Mandi dishes
- [ ] quickAddItem works for Mansaf
- [ ] Pricing calculates correctly
- [ ] Orders save to database
- [ ] SMS notifications work (if configured)

## Common Issues

### Issue: "Tool not found"
**Solution:** Check tool names in vapi-tools.json match server.py TOOLS dict

### Issue: "Webhook timeout"
**Solution:** Increase VAPI webhook timeout to 30 seconds for fresh Middle Eastern food prep

### Issue: "Menu items not recognized"
**Solution:** Check menu.json has correct item IDs and names

## Production Deployment

### Using Gunicorn (Recommended)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 stuffed_lamb.server:app
```

### Using HTTPS (Required for VAPI)
Use nginx or similar as reverse proxy with SSL certificate.

### Environment Variables
```bash
SHOP_NAME=Stuffed Lamb
SHOP_ADDRESS=210 Broadway, Reservoir VIC 3073
SHOP_TIMEZONE=Australia/Melbourne
SHOP_ORDER_TO=+61XXXXXXXXX  # Update with real number
```

## Support

For issues:
1. Check logs: `logs/stuffed_lamb.log`
2. Run tests: `pytest tests/`
3. Verify menu: `python -c "from stuffed_lamb.server import load_menu; load_menu()"`

## Differences from Kebabalab

| Feature | Kebabalab | Stuffed Lamb |
|---------|-----------|--------------|
| Main Items | Kebabs, HSP, Gözleme | Mandi, Mansaf |
| Combos | Yes (meals) | No |
| Pricing | $10-$25 | $23-$33 |
| Add-ons | Extras ($1-$4) | Nuts/Sultanas ($2), Jameed ($8.40) |
| Closed Days | None | Monday & Tuesday |

Both systems use the same 18 tools and server architecture.

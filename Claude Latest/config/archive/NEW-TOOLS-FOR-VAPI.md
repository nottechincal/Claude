# NEW TOOLS TO ADD TO VAPI

Add these 5 new tools to your VAPI assistant:

---

## 1. getOrderSummary

```json
{
  "type": "function",
  "function": {
    "name": "getOrderSummary",
    "description": "Get human-readable order summary to repeat back to customer before finalizing. Returns summary text and total.",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {},
      "required": []
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

## 2. setOrderNotes

```json
{
  "type": "function",
  "function": {
    "name": "setOrderNotes",
    "description": "Set special instructions or notes for the order. Use when customer says 'extra crispy', 'cut in half', 'no onion - allergic', etc.",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "notes": {
          "type": "string",
          "description": "Special instructions or notes for the order"
        }
      },
      "required": ["notes"]
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

## 3. getLastOrder

```json
{
  "type": "function",
  "function": {
    "name": "getLastOrder",
    "description": "Get customer's last order for repeat ordering. Use when customer says 'my usual' or you want to offer repeat order.",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "phoneNumber": {
          "type": "string",
          "description": "Customer's phone number"
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

## 4. lookupOrder

```json
{
  "type": "function",
  "function": {
    "name": "lookupOrder",
    "description": "Look up an existing order by order number or phone. Use when customer calls back about an existing order.",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "orderId": {
          "type": "string",
          "description": "Order number (e.g., '005', '123')"
        },
        "phoneNumber": {
          "type": "string",
          "description": "Customer's phone number"
        }
      },
      "required": []
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

## 5. sendMenuLink

```json
{
  "type": "function",
  "function": {
    "name": "sendMenuLink",
    "description": "Send menu link via SMS. Use when customer asks 'what's on the menu' or requests menu to be sent.",
    "strict": false,
    "parameters": {
      "type": "object",
      "properties": {
        "phoneNumber": {
          "type": "string",
          "description": "Customer's phone number to send menu link to"
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

## UPDATED: createOrder

**Important:** Update your existing createOrder tool to accept the `sendSMS` parameter:

```json
{
  "type": "function",
  "function": {
    "name": "createOrder",
    "description": "Create and save the final order. Pickup time must be set first via setPickupTime or estimateReadyTime. ALWAYS ask customer if they want receipt sent to their phone before calling this.",
    "strict": true,
    "parameters": {
      "type": "object",
      "properties": {
        "customerName": {
          "type": "string",
          "description": "Customer's name"
        },
        "customerPhone": {
          "type": "string",
          "description": "Customer's phone number"
        },
        "sendSMS": {
          "type": "boolean",
          "description": "Whether to send SMS receipt to customer (shop always gets SMS). Ask customer first."
        }
      },
      "required": ["customerName", "customerPhone"]
    }
  },
  "async": false,
  "server": {
    "url": "YOUR_WEBHOOK_URL/webhook"
  }
}
```

---

## Summary

**Total tools after adding these: 20 tools**

- 15 existing tools
- 5 new tools (getOrderSummary, setOrderNotes, getLastOrder, lookupOrder, sendMenuLink)
- 1 updated tool (createOrder - now accepts sendSMS parameter)

**All tools have:**
- `async: false`
- `strict: false` (except createOrder which is `strict: true`)

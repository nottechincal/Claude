# 🍽️ Kebabalab VAPI Phone Ordering System v3

**Enterprise-grade automated phone ordering with live cart modification and intelligent combo detection**

## 🌟 NEW in v3 - ENTERPRISE FEATURES

- ✅ **Live Cart Modification** - Remove items, edit sauces/salads, clear cart at any time during call
- ✅ **Lightning Fast** - Zero filler phrases, tools execute in milliseconds
- ✅ **Multi-Item Orders** - Handle complex orders with 5+ items in single utterance
- ✅ **Intelligent Parsing** - Extract ALL information from initial statement (no redundant questions)
- ✅ **13 Production Tools** - Complete order management with modification capabilities
- ✅ **Enterprise Prompt** - Optimized for speed, accuracy, and customer experience

## 📋 System Architecture

```
Customer Phone Call
       ↓
VAPI Assistant (AI Voice Agent)
       ↓ webhook
FastAPI Server (server_v2.py)
       ↓
SQLite Database (orders.db)
```

## 🛠️ Available Tools (13 Total)

### Core Order Flow
1. **checkOpen** - Check if shop is open
2. **getCallerInfo** - Get caller's phone number
3. **startItemConfiguration** - Begin configuring menu item
4. **setItemProperty** - Set size, protein, salads, sauces, etc.
5. **addItemToCart** - Add item and auto-detect combos
6. **getCartState** - View current cart contents

### Cart Modification (NEW in v3)
7. **removeCartItem** - Remove item by index
8. **editCartItem** - Modify salads, sauces, extras, quantity on existing items
9. **clearCart** - Start order from scratch

### Order Completion
10. **priceCart** - Calculate total with GST
11. **estimateReadyTime** - Estimate pickup time
12. **createOrder** - Save order to database
13. **endCall** - End the call

## 📁 Organized File Structure

```
kebabalab-vapi/
├── server_v2.py              # Main FastAPI server
├── menu.json                 # Menu with combo definitions
├── business.json             # Business details
├── hours.json                # Operating hours
├── rules.json                # Business rules
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
│
├── config/                   # Configuration files
│   ├── system-prompt-enterprise.md   # ENTERPRISE system prompt (USE THIS)
│   ├── system-prompt-optimized.md    # Optimized prompt (deprecated)
│   └── vapi-tools-definitions.json   # All 13 tool schemas
│
├── scripts/                  # PowerShell automation
│   ├── vapi-complete-setup.ps1       # Create all 10 original tools
│   ├── add-cart-tools.ps1            # Add 3 new cart tools
│   └── vapi-diagnostic.ps1           # Check tool status
│
├── tests/                    # Testing scripts
│   ├── test_tools_mega.py            # Comprehensive 40+ test suite
│   └── test_tools.py                 # Basic tests
│
├── docs/                     # Documentation
│   ├── README.md                     # Main documentation
│   ├── DEPLOYMENT_GUIDE.md           # Full deployment steps
│   ├── IMPLEMENTATION_SUMMARY.md     # Technical reference
│   ├── TESTING_SCENARIOS.md          # Test scenarios
│   └── TROUBLESHOOTING.md            # Common issues
│
└── archive/                  # Old/deprecated files
    ├── server.py                     # Original server
    ├── system-prompt.md              # Original prompt
    └── [old PowerShell scripts]
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Server
```bash
python server_v2.py
```

### 3. Expose with ngrok
```bash
ngrok http 8000
# Copy the HTTPS URL
```

### 4. Setup VAPI Tools

**Option A: Setup All Tools (First Time)**
```powershell
# Edit scripts/vapi-complete-setup.ps1 with your:
#   - ApiKey
#   - AssistantId
#   - WebhookUrl (your ngrok URL)

.\scripts\vapi-complete-setup.ps1
```

**Option B: Add Cart Tools Only (If you have 10 existing tools)**
```powershell
.\scripts\add-cart-tools.ps1
```

### 5. Update System Prompt

Copy the contents of `config/system-prompt-enterprise.md` to your VAPI assistant's system prompt in the dashboard.

### 6. Test Everything

```bash
python tests/test_tools_mega.py
```

This runs 40+ comprehensive tests covering all scenarios.

## 🎯 Key Capabilities

### Handle Complex Multi-Item Orders
```
Customer: "Small chicken kebab with lettuce tomato garlic sauce,
           large HSP with cheese all the sauces, chips, and two cokes"
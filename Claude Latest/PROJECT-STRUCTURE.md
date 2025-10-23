# 📁 Project Structure

```
Claude Latest/
│
├── 🔧 Core Files
│   ├── server_v2.py                    # Main VAPI server (FastAPI)
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Environment variables template
│   └── README.md                       # Project overview
│
├── 📊 Data Files
│   ├── business.json                   # Business details (phone, address, etc.)
│   ├── hours.json                      # Operating hours
│   ├── menu.json                       # Full menu with pricing
│   ├── rules.json                      # Order rules and policies
│   └── orders.db                       # SQLite database (orders, customers)
│
├── 📚 Documentation
│   ├── docs/business/                  # Cost analysis & business docs
│   │   ├── ACTUAL-COST-BREAKDOWN-FROM-YOUR-DATA.md
│   │   ├── COST-REDUCTION-ALTERNATIVES-REPORT.md
│   │   └── (other cost analysis docs)
│   │
│   ├── docs/technical/                 # Technical documentation
│   │   ├── CART-MANAGEMENT-FIX-SUMMARY.md
│   │   ├── CRITICAL-FIXES-SUMMARY.md
│   │   ├── SERVER-AUDIT-REPORT.md
│   │   └── TEST_REPORT.md
│   │
│   ├── docs/deployment/                # Deployment guides
│   │   ├── PRODUCTION-DEPLOYMENT-GUIDE.md
│   │   └── QUICK-DEPLOYMENT-GUIDE.md
│   │
│   └── docs/                           # Legacy docs (clean up later)
│       ├── DEPLOYMENT_GUIDE.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       └── TROUBLESHOOTING.md
│
├── ⚙️ Configuration
│   ├── config/system-prompt-*.md       # VAPI system prompts
│   ├── config/vapi-tools-definitions.json
│   └── config/NEW-TOOLS-FOR-VAPI.md
│
├── 🧪 Tests
│   ├── tests/test_critical_fixes.py
│   ├── tests/test_5_kebabs_meal_upgrade.py
│   ├── tests/test_cart_modifications.py
│   ├── tests/test_tools.py
│   └── tests/test_tools_mega.py
│
├── 📝 Logs
│   ├── logs/kebabalab_server.log       # Main production logs
│   └── logs/server.log                 # Legacy logs
│
├── 📦 Archive
│   └── archive/server.py               # Old server version
│
└── 🛠️ Scripts
    └── scripts/                        # Utility scripts

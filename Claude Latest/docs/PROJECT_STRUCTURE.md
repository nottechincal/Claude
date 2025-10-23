# 📁 PROJECT STRUCTURE - Kebabalab VAPI System

**Last Updated:** October 23, 2025
**Status:** ✅ Organized & Production-Ready

---

## 🌳 DIRECTORY TREE

```
/Claude Latest/
│
├── 📄 README.md                    # Project overview and quick start
├── 📄 PROJECT-STRUCTURE.md         # Old structure doc (deprecated)
├── 📄 .env.example                 # Environment variables template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 requirements.txt             # Python dependencies
│
├── 🐍 server_v2.py                 # Main FastAPI server (3,113 lines)
│
├── 📁 data/                        # Configuration data files
│   ├── menu.json                   # Complete menu with pricing
│   ├── business.json               # Business details
│   ├── hours.json                  # Operating hours
│   └── rules.json                  # Business rules & combos
│
├── 📁 config/                      # VAPI and system configuration
│   ├── vapi-tools-definitions.json # All 30 tool schemas for VAPI
│   ├── system-prompt-enterprise.md # Production VAPI system prompt
│   ├── system-prompt-optimized.md  # Alternative optimized prompt
│   ├── system-prompt-production.md # Production variant
│   └── NEW-TOOLS-FOR-VAPI.md       # New tools documentation
│
├── 📁 tests/                       # Comprehensive test suite
│   ├── test_tools_mega.py          # 40+ comprehensive tests
│   ├── test_comprehensive_edge_cases.py # 22 edge case tests
│   ├── test_cart_modifications.py  # Cart modification tests
│   ├── test_critical_fixes.py      # Bug fix validation
│   ├── test_5_kebabs_meal_upgrade.py # Complex order handling
│   ├── test_performance_enhancements.py # Performance tests
│   ├── test_edge_cases.py          # Edge case scenarios
│   ├── test_tools.py               # Basic tool tests
│   └── README_TESTS.md             # Testing guide
│
├── 📁 scripts/                     # Deployment & utility scripts
│   ├── vapi-complete-setup.ps1     # Deploy all tools to VAPI
│   ├── add-cart-tools.ps1          # Add cart management tools
│   ├── deploy-performance-tools.ps1 # Deploy performance tools
│   ├── vapi-diagnostic.ps1         # Diagnostic script
│   └── verify-tools.ps1            # Tool verification
│
├── 📁 docs/                        # Documentation (organized)
│   │
│   ├── 📁 reference/               # API and tool references
│   │   ├── COMPLETE_TOOLS_REFERENCE.md  # All 30 tools documented
│   │   ├── TOOLS_QUICK_REFERENCE.md     # Quick lookup card
│   │   ├── BUG_FIXES_SUMMARY.md         # Bug fixes documentation
│   │   └── WHATS-NEW.md                 # Latest features
│   │
│   ├── 📁 guides/                  # User and developer guides
│   │   ├── PERFORMANCE-ENHANCEMENTS.md  # Performance guide
│   │   └── TEST-SUITE-READY.md          # Testing guide
│   │
│   ├── 📁 deployment/              # Deployment documentation
│   │   ├── DEPLOYMENT_GUIDE.md          # Complete setup guide
│   │   ├── DEPLOYMENT-COMPLETE.md       # Deployment checklist
│   │   ├── VAPI-TOOLS-CHECKLIST.md      # VAPI deployment
│   │   ├── PRODUCTION-DEPLOYMENT-GUIDE.md # Production setup
│   │   └── QUICK-DEPLOYMENT-GUIDE.md    # Quick deploy
│   │
│   ├── 📁 technical/               # Technical deep-dives
│   │   ├── TEST_REPORT.md               # Test results (100% pass)
│   │   ├── IMPLEMENTATION_SUMMARY.md    # Technical reference
│   │   ├── SERVER-AUDIT-REPORT.md       # Server audit
│   │   ├── CART-MANAGEMENT-FIX-SUMMARY.md # Cart fixes
│   │   ├── CRITICAL-FIXES-SUMMARY.md    # Critical bug fixes
│   │   └── EDGE-CASE-TEST-PLAN.md       # Edge case testing
│   │
│   ├── 📁 business/                # Business analysis
│   │   ├── COST-ANALYSIS-AND-REDUCTION-STRATEGY.md
│   │   └── COST-BREAKDOWN-*.md          # Multiple cost reports
│   │
│   ├── 📄 README.md                # Main project documentation
│   ├── 📄 TESTING_SCENARIOS.md     # Test case scenarios
│   └── 📄 TROUBLESHOOTING.md       # Troubleshooting guide
│
├── 📁 logs/                        # Application logs
│   └── kebabalab_server.log        # Production server logs
│
├── 📁 data/                        # Runtime data
│   └── orders.db                   # SQLite database (auto-created)
│
├── 📁 backups/                     # Database backups
│   └── (backup files)              # Automated backups go here
│
├── 📁 archive/                     # Deprecated/old files
│   └── server.py                   # Original server (deprecated)
│
├── 📁 __pycache__/                 # Python cache files
│   └── (cached modules)
│
└── 📁 .claude/                     # Claude Code settings
    └── (configuration)

```

---

## 📂 DIRECTORY PURPOSES

### **Root Level**
- `server_v2.py` - Main application server
- Configuration files (.env, requirements.txt)
- Documentation overview (README.md)

### **data/**
- **Purpose:** Configuration data and menu information
- **Contents:** JSON configuration files
- **Access:** Read by server on startup
- **Caching:** Files cached in memory after first read

### **config/**
- **Purpose:** VAPI integration and system configuration
- **Contents:** Tool definitions and system prompts
- **Usage:** Deploy to VAPI platform
- **Updates:** Modify when adding/changing tools

### **tests/**
- **Purpose:** Comprehensive test suite
- **Coverage:** 100% pass rate (47 tests)
- **Run:** `pytest tests/`
- **Performance:** All tests complete in < 5 minutes

### **scripts/**
- **Purpose:** Deployment and maintenance scripts
- **Platform:** PowerShell (Windows)
- **Usage:** Deploy tools to VAPI, verify configuration

### **docs/**
- **Purpose:** All project documentation
- **Organization:** By type (reference, guides, deployment, technical)
- **Access:** Read by developers, operators, support

### **logs/**
- **Purpose:** Application logging
- **Rotation:** Manual (consider implementing auto-rotation)
- **Size:** Monitor for disk usage
- **Analysis:** Use for debugging and monitoring

### **data/** (runtime)
- **Purpose:** SQLite database and runtime data
- **Database:** orders.db (auto-created)
- **Backups:** Automated to backups/ folder
- **Size:** Grows with orders (monitor disk usage)

### **backups/**
- **Purpose:** Database backups
- **Frequency:** Recommended daily automated backups
- **Retention:** Keep last 30 days
- **Restore:** Use for disaster recovery

### **archive/**
- **Purpose:** Old/deprecated code
- **Usage:** Historical reference only
- **Cleanup:** Can be deleted if not needed

---

## 🗂️ FILE ORGANIZATION RULES

### **Configuration Files**
- Location: `/data/`
- Format: JSON
- Naming: lowercase with hyphens
- Validation: Must be valid JSON

### **Documentation Files**
- Location: `/docs/[category]/`
- Format: Markdown (.md)
- Naming: UPPERCASE-WITH-HYPHENS.md
- Organization: By purpose (reference, guides, etc.)

### **Log Files**
- Location: `/logs/`
- Format: Text with timestamps
- Naming: `{service}_server.log`
- Rotation: Implement log rotation in production

### **Data Files**
- Location: `/data/`
- Format: SQLite database
- Naming: `orders.db`
- Backups: Daily to `/backups/`

---

## 📦 DEPENDENCIES

### **Python Packages** (requirements.txt)
```
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
twilio==8.10.0
pytz==2023.3
```

### **System Requirements**
- Python 3.8+
- SQLite 3
- 1GB RAM minimum
- 10GB disk space

---

## 🔄 DATA FLOW

### **Startup**
```
server_v2.py starts
  ↓
Load environment (.env)
  ↓
Load config files (data/*.json)
  ↓
Initialize database (data/orders.db)
  ↓
Cache config in memory
  ↓
Start FastAPI server
```

### **Request Processing**
```
VAPI webhook → server_v2.py
  ↓
Tool function called
  ↓
Access session (in-memory)
  ↓
Access database (if needed)
  ↓
Return result to VAPI
  ↓
Log to logs/kebabalab_server.log
```

### **Data Storage**
```
Order created
  ↓
Saved to data/orders.db
  ↓
Backed up to backups/ (daily)
  ↓
SMS sent via Twilio
  ↓
Logged to logs/
```

---

## 🔐 SECURITY NOTES

### **Sensitive Files**
- `.env` - **NEVER commit to git**
- `data/orders.db` - Contains customer data
- `logs/` - May contain phone numbers

### **Safe to Commit**
- `.env.example` - Template only
- `data/*.json` - Public menu information
- `docs/` - Documentation
- `tests/` - Test code

---

## 🚀 DEPLOYMENT STRUCTURE

### **Development**
```
/Claude Latest/           # Development root
├── .env                  # Local config
├── server_v2.py          # Latest code
└── data/orders.db        # Dev database
```

### **Production**
```
/var/www/kebabalab/       # Production root
├── .env                  # Production config
├── server_v2.py          # Deployed code
├── data/
│   └── orders.db         # Production database
├── logs/
│   └── server.log        # Production logs
└── backups/
    └── orders-*.db       # Automated backups
```

---

## 📊 SIZE ESTIMATES

| Directory | Size | Growth Rate |
|-----------|------|-------------|
| server_v2.py | 112 KB | Stable |
| data/*.json | 20 KB | Slow |
| data/orders.db | 1-100 MB | 1 MB/month |
| logs/ | 10-500 MB | 50 MB/month |
| docs/ | 2 MB | Occasional |
| tests/ | 200 KB | Occasional |
| backups/ | 100 MB-1 GB | Cumulative |

---

## 🧹 MAINTENANCE

### **Daily**
- Monitor logs/ size
- Check data/orders.db size
- Backup database to backups/

### **Weekly**
- Review error logs
- Clean old log files (>30 days)
- Test backup restore

### **Monthly**
- Archive old backups
- Review disk usage
- Update documentation

---

## 🔧 QUICK REFERENCE

### **Key Files**
```bash
# Main server
./server_v2.py

# Configuration
./data/menu.json
./data/business.json
./.env

# Database
./data/orders.db

# Logs
./logs/kebabalab_server.log

# Tools reference
./docs/reference/COMPLETE_TOOLS_REFERENCE.md
```

### **Important Paths**
```python
# In server_v2.py
DB_PATH = "data/orders.db"
MENU_PATH = "data/menu.json"
LOG_PATH = "logs/kebabalab_server.log"
```

---

**Note:** This structure is optimized for:
- ✅ Easy navigation
- ✅ Clear separation of concerns
- ✅ Production deployment
- ✅ Version control
- ✅ Team collaboration
- ✅ System maintenance

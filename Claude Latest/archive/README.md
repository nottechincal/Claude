# 📁 Archive - Historical Files

This directory contains old code, reports, and configuration files from previous development phases.

⚠️ **DO NOT USE** - These files are kept for reference only.

---

## 📂 Contents

### old-reports/
Historical reports and documentation (archived Oct 30, 2025):
- `CODEBASE_ANALYSIS_REPORT.md` - Initial codebase analysis
- `COMPREHENSIVE_REVIEW.md` - Early system review
- `COMPREHENSIVE_TESTING_REPORT.md` - Initial testing report
- `COMPREHENSIVE_TEST_REPORT.md` - Mid-phase testing report
- `FINAL_REPORT_100_PERCENT.md` - 88-test milestone
- `SYSTEM_CHECK_FINDINGS.md` - System check results
- `DEPLOYMENT_CHECKLIST.md`, `DEPLOYMENT_STATUS.md`
- `VAPI_DASHBOARD_FIXES_REQUIRED.md`
- And 15+ other historical reports

**📊 Current Report:** `docs/ULTRA_COMPREHENSIVE_REPORT.md` (113 tests, 100% pass)

### old-servers/
Previous server versions:
- `server_v2.py` - Previous 22-tool server (had chip upgrade loop bug)
- `server.py` - Historical server backup

**🚀 Current Server:** `kebabalab/server.py` (18 tools, 2,600+ lines, 100% tested)

### old-system-prompts/
Historical VAPI configurations:
- `vapi-tools-definitions.json` - Old 22-tool definitions
- `system-prompt-*.md` - Various prompt versions (6 variants)
- `NEW-TOOLS-FOR-VAPI.md` - Tool change documentation
- `setPickupTime-tool.json` - Individual tool definitions

**⚙️ Current Config:**
- System Prompt: `config/system-prompt-simplified.md`
- Tools: `config/vapi-tools-simplified.json` (18 tools)

### old-tests/
Consolidated test files (archived Oct 30, 2025):
- `test_all_scenarios.py` - Early scenario testing
- `test_bug_fixes.py` - Bug fix verification
- `test_comprehensive_system.py` - System-wide tests
- `test_vapi_integration.py` - VAPI integration tests

**🧪 Current Tests:** `tests/test_comprehensive_coverage.py` (113 tests, 21 categories)

### old-scripts/
Archived PowerShell and Python scripts:
- `deploy-*.ps1` - Old deployment scripts (9 files)
- `vapi-*.ps1` - VAPI configuration scripts
- `fix-*.ps1` - Troubleshooting scripts

**🔧 Current Scripts:** `deployment/upload_tools_to_vapi.py`

---

## 📊 Evolution Timeline

### Phase 1: Initial System (22 tools)
- 22 VAPI tools
- Tool overlap issues
- Chip upgrade bug (20+ call loop)
- Customer hang-ups

### Phase 2: Simplified System (15 tools)
- Reduced to 15 tools
- Fixed chip upgrade bug
- 70% performance improvement
- Clean tool separation

### Phase 3: Current System (18 tools)
- 18 optimized tools
- 113 comprehensive tests (100% pass)
- Mixed protein pricing fix
- Edge case coverage
- Zero known bugs
- **Production ready**

---

## 🗂️ File Organization (Oct 30, 2025 Cleanup)

### What Was Moved

**Root → Archive:**
- 20+ markdown reports → `old-reports/`
- 4 test files → `old-tests/`
- VAPI config files → (already in archive)

**Result:**
- Clean root directory (only README, requirements, .env.example)
- Organized project structure
- Clear separation: active vs archived
- Easy navigation

---

## 🔍 Finding Current Versions

| Archived File | Current Location |
|--------------|------------------|
| `old-reports/*.md` | `docs/ULTRA_COMPREHENSIVE_REPORT.md` |
| `old-servers/server_v2.py` | `kebabalab/server.py` |
| `old-system-prompts/*.md` | `config/system-prompt-simplified.md` |
| `old-system-prompts/*.json` | `config/vapi-tools-simplified.json` |
| `old-tests/*.py` | `tests/test_comprehensive_coverage.py` |
| `old-scripts/*.ps1` | `deployment/upload_tools_to_vapi.py` |

---

## ⚠️ Important Notes

- **Do not use archived files** - They are outdated and potentially buggy
- **Refer to current documentation** - See main README.md
- **For historical context only** - Understand project evolution
- **No support for old versions** - Current system is production-ready

---

## 🚀 Current System Status

**Version:** 2.0
**Status:** ✅ Production Ready

**Metrics:**
- Tests: 113/113 passing (100%)
- Tools: 18 (optimized)
- Coverage: 100%
- Known Bugs: 0

**See:** `../README.md` for current system documentation

---

**Archive Last Updated:** October 30, 2025
**Cleanup Phase:** Repository organization and structure cleanup

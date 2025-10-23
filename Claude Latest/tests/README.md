# Test Files

## Critical Test

**test_chip_upgrade.py** - Tests the main bug fix

This test verifies:
- ✅ Chip upgrade works in 1 call (not 20+)
- ✅ Price updates correctly
- ✅ quickAddItem NLP parsing works
- ✅ All 15 tools function properly

Run it:
```bash
python tests/test_chip_upgrade.py
```

Expected output:
```
✓ TEST PASSED - Chip upgrade works in 1 call!
ALL TESTS PASSED!
```

## Other Tests

| File | Purpose |
|------|---------|
| test_tools.py | Basic tool functionality |
| test_tools_mega.py | Comprehensive tool testing |
| test_cart_modifications.py | Cart modification scenarios |
| test_critical_fixes.py | Critical bug fixes |
| test_edge_cases.py | Edge case handling |
| test_comprehensive_edge_cases.py | Extended edge cases |
| test_performance_enhancements.py | Performance optimizations |
| test_5_kebabs_meal_upgrade.py | Meal upgrade scenarios |

## Running Tests

```bash
# Run critical test
python tests/test_chip_upgrade.py

# Run all tests
pytest tests/

# Run specific test
python tests/test_cart_modifications.py
```

## Test Data

Tests use:
- Mock VAPI webhook calls
- In-memory sessions
- Temporary database
- Menu from `../data/menu.json`

## What to Test Before Deployment

**Minimum:**
1. `test_chip_upgrade.py` - Must pass

**Recommended:**
2. `test_cart_modifications.py`
3. `test_critical_fixes.py`

**Full regression:**
- Run all tests with `pytest tests/`

## See Also

- `../deployment/DEPLOYMENT_CHECKLIST.md` - Pre-deployment testing
- `../docs/TESTING_SCENARIOS.md` - Manual test scenarios

#!/bin/bash
# ======================================
# Stuffed Lamb - Setup Verification Script
# ======================================
# Checks if the system is properly configured before running

set -e

echo ""
echo "===================================="
echo "Stuffed Lamb Setup Verification"
echo "===================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check 1: Python version
echo -n "Checking Python version... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 8 ]; then
        echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}✗ Python $PYTHON_VERSION (need 3.8+)${NC}"
        ERRORS=$((ERRORS+1))
    fi
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check 2: .env file exists
echo -n "Checking .env file... "
if [ -f .env ]; then
    echo -e "${GREEN}✓ Found${NC}"

    # Check for placeholder values
    if grep -q "your_twilio_account_sid_here\|your_twilio_auth_token_here" .env 2>/dev/null; then
        echo -e "${YELLOW}  ⚠ Warning: Placeholder Twilio credentials detected${NC}"
        WARNINGS=$((WARNINGS+1))
    fi

    if grep -q "+61xxxxxxxxxx\|+61XXXXXXXXX" .env 2>/dev/null; then
        echo -e "${YELLOW}  ⚠ Warning: Placeholder phone numbers detected${NC}"
        WARNINGS=$((WARNINGS+1))
    fi

    # Check for required variables
    echo -n "  Checking SHOP_ORDER_TO... "
    if grep -q "^SHOP_ORDER_TO=" .env; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗ Missing${NC}"
        ERRORS=$((ERRORS+1))
    fi

else
    echo -e "${RED}✗ Not found${NC}"
    echo -e "${YELLOW}  Run: cp .env.example .env${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check 3: Required data files
echo -n "Checking data files... "
REQUIRED_FILES=("data/menu.json" "data/hours.json" "data/business.json" "data/rules.json")
MISSING_FILES=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        if [ $MISSING_FILES -eq 0 ]; then
            echo -e "${RED}✗${NC}"
        fi
        echo -e "${RED}  Missing: $file${NC}"
        MISSING_FILES=$((MISSING_FILES+1))
        ERRORS=$((ERRORS+1))
    fi
done
if [ $MISSING_FILES -eq 0 ]; then
    echo -e "${GREEN}✓ All present${NC}"
fi

# Check 4: Python dependencies
echo -n "Checking Python dependencies... "
if python3 -c "import flask, twilio, redis, pytz, rapidfuzz" 2>/dev/null; then
    echo -e "${GREEN}✓ Installed${NC}"
else
    echo -e "${RED}✗ Missing${NC}"
    echo -e "${YELLOW}  Run: pip install -r requirements.txt${NC}"
    ERRORS=$((ERRORS+1))
fi

# Check 5: Redis (optional)
echo -n "Checking Redis... "
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${YELLOW}⚠ Installed but not running${NC}"
        echo -e "${YELLOW}  System will use in-memory sessions${NC}"
        WARNINGS=$((WARNINGS+1))
    fi
else
    echo -e "${YELLOW}⚠ Not installed${NC}"
    echo -e "${YELLOW}  System will use in-memory sessions (OK for development)${NC}"
    WARNINGS=$((WARNINGS+1))
fi

# Check 6: Port 8000 availability
echo -n "Checking port 8000... "
if netstat -tuln 2>/dev/null | grep -q ":8000 " || ss -tuln 2>/dev/null | grep -q ":8000 "; then
    echo -e "${YELLOW}⚠ Already in use${NC}"
    WARNINGS=$((WARNINGS+1))
else
    echo -e "${GREEN}✓ Available${NC}"
fi

# Summary
echo ""
echo "===================================="
echo "Summary:"
echo "===================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! System is ready to run.${NC}"
    echo ""
    echo "To start the server:"
    echo "  ./start.sh           # Linux/Mac"
    echo "  start.bat            # Windows"
    echo "  python run.py        # Direct"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) - system should work${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before running."
    exit 1
fi

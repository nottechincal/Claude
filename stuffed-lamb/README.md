# Stuffed Lamb - Automated Ordering System

Automated voice and online ordering system for Stuffed Lamb Middle Eastern Restaurant in Reservoir, VIC.

## 🏪 Business Information

- **Name:** Stuffed Lamb
- **Location:** 210 Broadway, Reservoir VIC 3073
- **Cuisine:** Middle Eastern
- **Rating:** ⭐ 4.5
- **Website:** https://stuffed-lamb.tuckerfox.com.au/

## 📋 Menu Overview

### Main Dishes

1. **Jordanian Mansaf** - $33.00
   - Traditional Jordanian dish with slow-cooked lamb neck in dried yogurt sauce (Jameed)
   - Served with rice garnished with nuts
   - Extras available: Extra Jameed (+$8.40), Extra Rice (+$8.40)

2. **Lamb Mandi** - $28.00
   - Tender lamb neck meat on rice with Arabic spices
   - Garnished with green chilli, potatoes, and onions
   - Served with Tzatziki and Chilli Mandi Sauce
   - Add-ons: Nuts (+$2.00), Sultanas (+$2.00)
   - Extras: Green Chillis, Potato, Tzatziki, Chilli Sauce (+$1.00 each), Extra Rice on Plate (+$5.00)

3. **Chicken Mandi** - $23.00
   - Half chicken on rice with Arabic spices
   - Garnished with green chilli, parsley, and potatoes
   - Served with Tzatziki and Chilli Mandi Sauce
   - Same add-ons and extras as Lamb Mandi

### Soups & Sides

- **Soup of the Day** - $7.00
- **Rice** (side portion) - $7.00

### Drinks

- **Soft Drinks (Can)** - $3.00
  - Coke, Coke No Sugar, Sprite, L&P, Fanta
- **Bottle of Water** - $2.00

### Extras ($1.00 each unless noted)

- Nuts
- Sultanas
- Tzatziki
- Chilli Mandi Sauce
- Bread
- Green Chilli
- Potato
- Rice (side) - $7.00
- Extra Rice on Plate - $5.00

## 🕐 Operating Hours

| Day | Hours |
|-----|-------|
| Monday | **CLOSED** |
| Tuesday | **CLOSED** |
| Wednesday | 1:00 PM - 9:00 PM |
| Thursday | 1:00 PM - 9:00 PM |
| Friday | 1:00 PM - 9:00 PM |
| Saturday | 1:00 PM - 10:00 PM |
| Sunday | 1:00 PM - 10:00 PM |

## 🚀 Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Clone or navigate to this directory:**
   ```bash
   cd stuffed-lamb
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database:**
   ```bash
   python -c "from stuffed_lamb.server import init_database; init_database()"
   ```

## 🧪 Running Tests

Run the comprehensive test suite:

```bash
# Run all tests
pytest tests/test_stuffed_lamb_system.py -v

# Run specific test class
pytest tests/test_stuffed_lamb_system.py::TestMainDishes -v

# Run with coverage
pytest tests/test_stuffed_lamb_system.py --cov=stuffed_lamb --cov-report=html
```

### Test Coverage

The test suite covers:
- ✅ Menu loading and validation
- ✅ All main dishes pricing
- ✅ Add-ons and modifiers
- ✅ Complex pricing calculations
- ✅ Drinks and sides
- ✅ Multi-item orders
- ✅ GST calculations
- ✅ Business hours
- ✅ Configuration validation

## 🏃 Running the Server

### Development Mode

```bash
python -m stuffed_lamb.server
```

The server will start on `http://localhost:5000`

### Production Mode

```bash
# Using Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:5000 stuffed_lamb.server:app

# Or using Flask's built-in server (not recommended for production)
export FLASK_APP=stuffed_lamb.server
flask run --host=0.0.0.0 --port=5000
```

## 📁 Project Structure

```
stuffed-lamb/
├── stuffed_lamb/          # Main application package
│   ├── __init__.py
│   └── server.py          # Flask server with all business logic
├── data/                  # Configuration and menu data
│   ├── menu.json          # Complete menu with pricing
│   ├── business.json      # Business details and settings
│   ├── hours.json         # Operating hours
│   └── rules.json         # Business rules and policies
├── tests/                 # Test suite
│   └── test_stuffed_lamb_system.py
├── logs/                  # Application logs (auto-created)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore
└── README.md             # This file
```

## 💰 Pricing Examples

### Example 1: Lamb Mandi with Add-ons
```
Lamb Mandi (base)         $28.00
+ Add Nuts                + $2.00
+ Add Sultanas            + $2.00
+ Extra Green Chilli      + $1.00
+ Extra Potato            + $1.00
+ Extra Rice on Plate     + $5.00
                          -------
TOTAL                     $39.00
```

### Example 2: Chicken Mandi Simple
```
Chicken Mandi (base)      $23.00
+ Add Nuts                + $2.00
                          -------
TOTAL                     $25.00
```

### Example 3: Jordanian Mansaf Deluxe
```
Jordanian Mansaf (base)   $33.00
+ Extra Jameed            + $8.40
+ Extra Rice              + $8.40
                          -------
TOTAL                     $49.80
```

### Example 4: Family Order
```
1× Mansaf                 $33.00
1× Lamb Mandi + Nuts      $30.00
1× Chicken Mandi          $23.00
3× Soft Drinks @ $3.00    + $9.00
1× Soup of the Day        + $7.00
                          -------
SUBTOTAL                 $102.00
GST (included)            ~$9.27
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Business Details
SHOP_NAME=Stuffed Lamb
SHOP_ADDRESS=210 Broadway, Reservoir VIC 3073
SHOP_TIMEZONE=Australia/Melbourne

# GST (Australian Goods and Services Tax)
GST_RATE=0.10

# Session Management
SESSION_TTL=1800          # 30 minutes
MAX_SESSIONS=1000

# Redis (optional, for production)
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 📊 Features

- ✅ Complete menu with all items and pricing
- ✅ Add-ons system (nuts, sultanas for Mandi dishes)
- ✅ Flexible extras system
- ✅ GST-inclusive pricing
- ✅ Operating hours management
- ✅ Session management (Redis or in-memory)
- ✅ Order database with SQLite
- ✅ Comprehensive error handling
- ✅ Extensive test coverage
- ✅ VAPI integration ready
- ✅ Fuzzy matching for voice orders

## 🎯 Key Differences from Kebabalab System

This system is tailored specifically for Stuffed Lamb:

1. **Simpler Menu Structure:** Focus on 3 main dishes instead of many variants
2. **Different Add-ons:** Nuts/Sultanas system for Mandi dishes
3. **Unique Extras:** Mansaf-specific extras (Jameed, special rice portions)
4. **Different Hours:** Closed Monday-Tuesday, different closing times
5. **Different Pricing:** Premium pricing for specialty Middle Eastern dishes
6. **No Combos:** Individual items only, no combo deals

## 📝 Notes

- All prices include 10% GST (Australian tax)
- 10% service charge applies to **dine-in only** (not takeaway/online orders)
- Closed Mondays and Tuesdays
- Mandi dishes come with default garnishes and sauces
- Mansaf includes nuts by default
- L&P (Lemon & Paeroa) is available for those who prefer it!

## 🐛 Troubleshooting

### Tests failing?
```bash
# Make sure menu data is valid
python -c "from stuffed_lamb.server import load_menu; load_menu()"

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Server not starting?
```bash
# Check if port 5000 is available
lsof -i :5000

# Try a different port
python -m stuffed_lamb.server --port=8080
```

## 📞 Support

For issues or questions about this system, check:
1. Test results: `pytest tests/ -v`
2. Logs: `logs/stuffed_lamb.log`
3. Configuration: `data/*.json`

## 📜 License

Proprietary - Built for Stuffed Lamb Restaurant

---

**Built with ❤️ for authentic Middle Eastern cuisine**

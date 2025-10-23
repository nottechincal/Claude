"""
Kebabalab VAPI Server - SIMPLIFIED VERSION
============================================

15 focused tools, zero overlap, maximum clarity.

Design principles:
- One tool, one purpose
- All editing in ONE call
- Fast NLP parsing
- Clear error messages
- Simple is better

"""

import json
import logging
import os
import sqlite3
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except ModuleNotFoundError:  # pragma: no cover - exercised only in CI without Flask
    # Minimal fallbacks so tests can run in environments without Flask installed.
    from types import SimpleNamespace

    class _RequestProxy:
        def __init__(self):
            self._stack: List[SimpleNamespace] = []

        def push(self, payload: Dict[str, Any]):
            self._stack.append(SimpleNamespace(json=payload))

        def pop(self):
            if self._stack:
                self._stack.pop()

        def get_json(self, *_, **__):
            if not self._stack:
                return {}
            return self._stack[-1].json or {}

    class _TestRequestContext:
        def __init__(self, app: "Flask", json: Optional[Dict[str, Any]] = None):
            self.app = app
            self.json = json or {}

        def __enter__(self):
            request.push(self.json)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            request.pop()

    class Flask:  # type: ignore
        def __init__(self, name: str):
            self.name = name

        def route(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

        def get(self, *args, **kwargs):
            return self.route(*args, **kwargs)

        def post(self, *args, **kwargs):
            return self.route(*args, **kwargs)

        def test_request_context(self, json: Optional[Dict[str, Any]] = None):
            return _TestRequestContext(self, json=json)

        def run(self, *_, **__):
            raise RuntimeError("Flask is not installed in this environment")

    def jsonify(payload: Dict[str, Any]):
        return payload

    def CORS(_app):  # noqa: N802 - matching Flask extension signature
        return _app

    request = _RequestProxy()

# ==================== CONFIGURATION ====================

app = Flask(__name__)
CORS(app)

# Logging
# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/kebabalab_simplified.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
MENU_FILE = os.path.join(DATA_DIR, 'menu.json')
DB_FILE = os.path.join(DATA_DIR, 'orders.db')

# Global menu
MENU = {}

# In-memory sessions (in production, use Redis)
SESSIONS = {}

# ==================== DATABASE ====================

def init_database():
    """Initialize SQLite database for orders"""
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            cart_json TEXT NOT NULL,
            subtotal REAL NOT NULL,
            gst REAL NOT NULL,
            total REAL NOT NULL,
            ready_at TEXT,
            notes TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Database initialized")

# ==================== MENU ====================

def load_menu():
    """Load menu from JSON file"""
    global MENU
    try:
        with open(MENU_FILE, 'r', encoding='utf-8') as f:
            MENU = json.load(f)
        logger.info(f"Menu loaded successfully from {MENU_FILE}")
        return True
    except Exception as e:
        logger.error(f"Failed to load menu: {e}")
        return False

# ==================== SESSION MANAGEMENT ====================

def get_session_id() -> str:
    """Get session ID from request (phone number or call ID)"""
    data = request.get_json() or {}
    message = data.get('message', {})

    # Try to get phone number from call
    phone = message.get('call', {}).get('customer', {}).get('number', '')
    if phone:
        return phone

    # Fallback to call ID
    call_id = message.get('call', {}).get('id', 'default')
    return call_id

def session_get(key: str, default=None):
    """Get value from session"""
    session_id = get_session_id()
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {}
    return SESSIONS[session_id].get(key, default)

def session_set(key: str, value: Any):
    """Set value in session"""
    session_id = get_session_id()
    if session_id not in SESSIONS:
        SESSIONS[session_id] = {}
    SESSIONS[session_id][key] = value

# ==================== HELPER FUNCTIONS ====================

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    if not text:
        return ""
    return text.lower().strip()

def parse_protein(text: str) -> Optional[str]:
    """Extract protein type from text"""
    text = normalize_text(text)

    if any(word in text for word in ['lamb', 'lamp']):
        return 'lamb'
    if any(word in text for word in ['chicken', 'chiken', 'chkn']):
        return 'chicken'
    if 'mix' in text or 'mixed' in text:
        return 'mixed'
    if 'falafel' in text or 'vegan' in text:
        return 'falafel'

    return None

def parse_size(text: str) -> Optional[str]:
    """Extract size from text"""
    text = normalize_text(text)

    if not text:
        return None

    # Match explicit words first to avoid substring collisions (e.g. "small" containing "l ")
    if re.search(r"\bsmall\b", text):
        return 'small'
    if re.search(r"\bs\b", text):
        return 'small'

    if re.search(r"\blarge\b", text) or re.search(r"\bbig\b", text):
        return 'large'
    if re.search(r"\bl\b", text):
        return 'large'

    return None

def parse_salads(text: str) -> List[str]:
    """Extract salads from text"""
    text = normalize_text(text)
    salads = []

    if 'lettuce' in text:
        salads.append('lettuce')
    if 'tomato' in text:
        salads.append('tomato')
    if 'onion' in text:
        salads.append('onion')
    if 'pickle' in text:
        salads.append('pickles')
    if 'olive' in text:
        salads.append('olives')

    # Check for "no salad"
    if any(phrase in text for phrase in ['no salad', 'without salad', 'hold salad']):
        return []

    return salads

def parse_sauces(text: str) -> List[str]:
    """Extract sauces from text"""
    text = normalize_text(text)
    sauces = []

    if 'garlic' in text or 'garlek' in text:
        sauces.append('garlic')
    if 'chili' in text or 'chilli' in text:
        sauces.append('chilli')
    if 'bbq' in text:
        sauces.append('bbq')
    if 'tomato sauce' in text or 'ketchup' in text:
        sauces.append('tomato')
    if 'sweet chilli' in text or 'sweet chili' in text:
        sauces.append('sweet chilli')
    if 'mayo' in text or 'aioli' in text:
        sauces.append('mayo')
    if 'hummus' in text:
        sauces.append('hummus')

    # Check for "no sauce"
    if any(phrase in text for phrase in ['no sauce', 'without sauce', 'hold sauce']):
        return []

    return sauces


def parse_extras(text: str) -> List[str]:
    """Extract extras such as cheese or haloumi from text."""
    text = normalize_text(text)
    extras: List[str] = []

    extra_keywords = {
        "cheese": ["cheese", "extra cheese", "add cheese", "with cheese"],
        "haloumi": ["haloumi", "halloumi"],
        "jalapenos": ["jalapeno", "jalapeño", "jalapenos"],
        "olives": ["olive", "olives"],
        "extra meat": ["extra meat", "more meat", "double meat"],
    }

    for extra, keywords in extra_keywords.items():
        if any(keyword in text for keyword in keywords):
            extras.append(extra)

    return extras

def parse_quantity(text: str) -> int:
    """Extract quantity from text"""
    text = normalize_text(text)

    # Look for numbers at the start
    match = re.match(r'^(\d+)', text.strip())
    if match:
        return int(match.group(1))

    # Look for words
    word_numbers = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }

    for word, num in word_numbers.items():
        if text.startswith(word):
            return num

    return 1

def calculate_price(item: Dict) -> float:
    """Calculate price for a single item"""
    price = 0.0

    # If it's a combo/meal, use combo price
    if item.get('is_combo'):
        return item.get('price', 0.0)

    # Base price from category
    category = item.get('category', '')
    size = item.get('size', 'small')

    if category == 'kebabs':
        price = 10.0 if size == 'small' else 15.0
    elif category == 'hsp':
        price = 15.0 if size == 'small' else 20.0
    elif category == 'chips':
        price = 5.0 if size == 'small' else 9.0
    elif category == 'drinks':
        price = 3.5
    elif category == 'gozleme':
        price = 15.0
    elif category == 'sweets':
        # Specific sweet items
        name = item.get('name', '').lower()
        if 'baklava' in name:
            if 'pack' in name or '4' in name:
                price = 10.0
            else:
                price = 3.0
        elif 'turkish delight' in name:
            price = 1.0
        elif 'rice pudding' in name:
            price = 5.0
    elif category == 'sauce_tubs':
        price = 1.0

    # Add extras
    extras = item.get('extras', [])
    for extra in extras:
        if extra in ['haloumi', 'halloumi']:
            price += 2.5
        elif extra in ['extra meat', 'extra lamb', 'extra chicken']:
            price += 3.0
        elif extra == 'cheese':
            price += 1.0
        elif extra in ['olives', 'jalapenos']:
            price += 1.0

    return price

def format_cart_item(item: Dict, index: int) -> str:
    """Format a cart item for human reading"""
    parts = []

    # Quantity
    qty = item.get('quantity', 1)
    if qty > 1:
        parts.append(f"{qty}x")

    # Size
    size = item.get('size', '')
    if size:
        parts.append(size.capitalize())

    # Protein
    protein = item.get('protein', '')
    if protein:
        parts.append(protein.capitalize())

    # Category/Name
    category = item.get('category', '').title()
    name = item.get('name', category)
    if not name:
        name = category
    parts.append(name)

    # Combo info
    if item.get('is_combo'):
        combo_parts = []
        chips_size = item.get('chips_size', 'small')
        if chips_size:
            combo_parts.append(f"{chips_size} chips")
        drink = item.get('drink_brand', 'Coke')
        if drink:
            combo_parts.append(drink)
        if combo_parts:
            parts.append(f"({', '.join(combo_parts)})")

    # Salads
    salads = item.get('salads', [])
    if salads:
        parts.append(f"w/ {', '.join(salads)}")

    # Sauces
    sauces = item.get('sauces', [])
    if sauces:
        parts.append(f"+ {', '.join(sauces)} sauce")

    # Extras
    extras = item.get('extras', [])
    if extras:
        parts.append(f"+ {', '.join(extras)}")

    # Price
    price = calculate_price(item) * qty
    parts.append(f"- ${price:.2f}")

    return f"{index}. {' '.join(parts)}"

# ==================== TOOL IMPLEMENTATIONS ====================

# Tool 1: checkOpen
def tool_check_open(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check if shop is currently open"""
    try:
        now = datetime.now()
        day_of_week = now.weekday()  # 0 = Monday, 6 = Sunday
        current_time = now.strftime("%H:%M")

        # Shop hours (example)
        # Monday-Thursday: 11:00-22:00
        # Friday-Saturday: 11:00-23:00
        # Sunday: 11:00-21:00

        if day_of_week in [0, 1, 2, 3]:  # Mon-Thu
            open_time, close_time = "11:00", "22:00"
        elif day_of_week in [4, 5]:  # Fri-Sat
            open_time, close_time = "11:00", "23:00"
        else:  # Sunday
            open_time, close_time = "11:00", "21:00"

        is_open = open_time <= current_time < close_time

        return {
            "ok": True,
            "isOpen": is_open,
            "currentTime": current_time,
            "openTime": open_time,
            "closeTime": close_time,
            "message": f"We're {'open' if is_open else 'closed'}. Hours today: {open_time}-{close_time}"
        }
    except Exception as e:
        logger.error(f"Error checking open status: {e}")
        return {"ok": False, "error": str(e)}

# Tool 2: getCallerSmartContext
def tool_get_caller_smart_context(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get caller info with order history and smart suggestions"""
    try:
        data = request.get_json() or {}
        message = data.get('message', {})
        call = message.get('call', {})
        customer = call.get('customer', {})

        phone = customer.get('number', 'unknown')

        # Get order history from database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT order_number, cart_json, total, created_at
            FROM orders
            WHERE customer_phone = ?
            ORDER BY created_at DESC
            LIMIT 5
        ''', (phone,))

        orders = cursor.fetchall()
        conn.close()

        order_history = []
        favorite_items = {}

        for order in orders:
            order_num, cart_json, total, created_at = order
            cart = json.loads(cart_json)

            order_history.append({
                "orderNumber": order_num,
                "total": total,
                "date": created_at,
                "itemCount": len(cart)
            })

            # Track item frequency
            for item in cart:
                item_key = f"{item.get('size', '')} {item.get('protein', '')} {item.get('category', '')}"
                favorite_items[item_key] = favorite_items.get(item_key, 0) + 1

        # Find most ordered item
        most_ordered = None
        if favorite_items:
            most_ordered = max(favorite_items, key=favorite_items.get)

        # Greeting suggestions
        is_returning = len(orders) > 0
        greeting_suggestion = "Welcome back!" if is_returning else "Welcome to Kebabalab!"

        return {
            "ok": True,
            "phone": phone,
            "isReturningCustomer": is_returning,
            "orderCount": len(orders),
            "orderHistory": order_history[:3],  # Last 3 orders
            "mostOrderedItem": most_ordered,
            "greetingSuggestion": greeting_suggestion,
            "canRepeatOrder": len(orders) > 0
        }

    except Exception as e:
        logger.error(f"Error getting caller context: {e}")
        return {
            "ok": True,
            "phone": "unknown",
            "isReturningCustomer": False,
            "orderCount": 0
        }

# Tool 3: quickAddItem
def tool_quick_add_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Smart NLP parser - add items from natural language.

    Examples:
    - "large lamb kebab with garlic sauce and lettuce"
    - "2 cokes"
    - "small chicken hsp no salad"
    """
    try:
        description = params.get('description', '').strip()

        if not description:
            return {"ok": False, "error": "description is required"}

        logger.info(f"QuickAddItem: parsing '{description}'")

        # Parse quantity
        quantity = parse_quantity(description)

        # Parse category
        desc_lower = normalize_text(description)
        category = None
        item_name = ""

        if 'kebab' in desc_lower or 'doner' in desc_lower:
            category = 'kebabs'
            item_name = "Kebab"
        elif 'hsp' in desc_lower:
            category = 'hsp'
            item_name = "HSP"
        elif 'chips' in desc_lower or 'fries' in desc_lower:
            category = 'chips'
            item_name = "Chips"
        elif any(drink in desc_lower for drink in ['coke', 'sprite', 'fanta', 'pepsi', 'drink']):
            category = 'drinks'
            # Determine brand
            for brand in ['coca-cola', 'coke', 'sprite', 'fanta', 'pepsi', 'water']:
                if brand in desc_lower:
                    item_name = brand.capitalize()
                    break
            if not item_name:
                item_name = "Coke"  # default
        elif 'gozleme' in desc_lower:
            category = 'gozleme'
            item_name = "Gözleme"
        else:
            return {
                "ok": False,
                "error": f"Couldn't determine item type from '{description}'. Please be more specific."
            }

        # Parse size
        size = parse_size(description)
        if not size and category in ['kebabs', 'hsp', 'chips']:
            # Default to large for kebabs/hsp, small for chips
            size = 'large' if category in ['kebabs', 'hsp'] else 'small'

        # Parse protein (for kebabs/hsp)
        protein = None
        if category in ['kebabs', 'hsp']:
            protein = parse_protein(description)
            if not protein:
                protein = 'chicken'  # default
            item_name = f"{protein.capitalize()} {item_name}"

        # Parse salads
        salads = parse_salads(description)

        # Parse sauces
        sauces = parse_sauces(description)

        # Parse extras/add-ons
        extras = parse_extras(description)

        # Create item
        item = {
            "category": category,
            "name": f"{size.capitalize()} {item_name}" if size else item_name,
            "size": size,
            "protein": protein,
            "salads": salads,
            "sauces": sauces,
            "extras": extras,
            "quantity": quantity,
            "is_combo": False,
            "cheese": "cheese" in extras,
        }

        # Calculate price
        item['price'] = calculate_price(item)

        # Add to cart
        cart = session_get('cart', [])
        cart.append(item)
        session_set('cart', cart)
        session_set('cart_priced', False)

        logger.info(f"Added to cart: {item}")

        return {
            "ok": True,
            "message": f"Added {quantity}x {item['name']} to cart",
            "item": item,
            "cartSize": len(cart)
        }

    except Exception as e:
        logger.error(f"Error in quickAddItem: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}

# Tool 4: addMultipleItemsToCart
def tool_add_multiple_items_to_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add multiple fully configured items to cart in one call"""
    try:
        items = params.get('items', [])

        if not items:
            return {"ok": False, "error": "items array is required"}

        cart = session_get('cart', [])
        added_count = 0

        for item_config in items:
            # Build item
            item = {
                "category": item_config.get('category', ''),
                "name": item_config.get('name', ''),
                "size": item_config.get('size'),
                "protein": item_config.get('protein'),
                "salads": item_config.get('salads', []),
                "sauces": item_config.get('sauces', []),
                "extras": item_config.get('extras', []),
                "cheese": item_config.get('cheese', False),
                "quantity": item_config.get('quantity', 1),
                "brand": item_config.get('brand'),
                "salt_type": item_config.get('salt_type', 'chicken'),
                "is_combo": False
            }

            # Calculate price
            item['price'] = calculate_price(item)

            cart.append(item)
            added_count += 1

        session_set('cart', cart)
        session_set('cart_priced', False)

        return {
            "ok": True,
            "message": f"Added {added_count} items to cart",
            "cartSize": len(cart)
        }

    except Exception as e:
        logger.error(f"Error adding multiple items: {e}")
        return {"ok": False, "error": str(e)}

# Tool 5: getCartState
def tool_get_cart_state(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get current cart contents - both structured and formatted"""
    try:
        cart = session_get('cart', [])

        # Format items for human reading
        formatted_items = []
        for idx, item in enumerate(cart):
            formatted_items.append(format_cart_item(item, idx))

        return {
            "ok": True,
            "cart": cart,  # Structured data
            "formattedItems": formatted_items,  # Human-readable
            "itemCount": len(cart),
            "isEmpty": len(cart) == 0
        }

    except Exception as e:
        logger.error(f"Error getting cart state: {e}")
        return {"ok": False, "error": str(e)}

# Tool 6: removeCartItem
def tool_remove_cart_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove item from cart by index"""
    try:
        item_index = params.get('itemIndex')

        if item_index is None:
            return {"ok": False, "error": "itemIndex is required"}

        cart = session_get('cart', [])

        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            return {"ok": False, "error": "itemIndex must be a number"}

        if item_index < 0 or item_index >= len(cart):
            return {"ok": False, "error": f"Invalid itemIndex. Cart has {len(cart)} items (0-{len(cart)-1})"}

        removed_item = cart.pop(item_index)
        session_set('cart', cart)
        session_set('cart_priced', False)

        return {
            "ok": True,
            "message": f"Removed item at index {item_index}",
            "removedItem": removed_item,
            "cartSize": len(cart)
        }

    except Exception as e:
        logger.error(f"Error removing cart item: {e}")
        return {"ok": False, "error": str(e)}

# Tool 7: editCartItem - THE CRITICAL ONE
_MOD_KEY_CANDIDATES: Tuple[str, ...] = (
    "property",
    "name",
    "field",
    "key",
    "attribute",
    "path",
    "propertyName",
    "prop",
)

_MOD_VALUE_CANDIDATES: Tuple[str, ...] = (
    "value",
    "newValue",
    "new_value",
    "values",
    "val",
    "propertyValue",
)


def _coerce_key_value(entry: Dict[str, Any]) -> Optional[Tuple[str, Any]]:
    """Extract a key/value pair from a mapping if it stores the data indirectly."""
    key = None
    for candidate in _MOD_KEY_CANDIDATES:
        if candidate in entry and entry[candidate] not in (None, ""):
            key = str(entry[candidate])
            break

    if not key:
        return None

    for candidate in _MOD_VALUE_CANDIDATES:
        if candidate in entry:
            return key, entry[candidate]

    # Some payloads provide the value under the derived key
    if key in entry:
        return key, entry[key]

    return None


def _normalise_mapping(mapping: Dict[str, Any], parent_key: Optional[str] = None) -> Dict[str, Any]:
    extracted = _coerce_key_value(mapping)
    if extracted:
        key, value = extracted
        return {key: value}

    if parent_key:
        for candidate in _MOD_VALUE_CANDIDATES:
            if candidate in mapping:
                return {parent_key: mapping[candidate]}

    normalised: Dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, dict):
            extracted_child = _coerce_key_value(value)
            if extracted_child and extracted_child[0] == key:
                normalised[key] = extracted_child[1]
                continue
            nested = _normalise_mapping(value, parent_key=key)
            for nested_key, nested_value in nested.items():
                normalised[nested_key] = nested_value
        else:
            normalised[key] = value

    # If the mapping only contained helper keys (like property/value) recurse once more
    if not normalised:
        return {}

    # Collapse cases where recursion produced {"value": "large"}
    extracted_again = _coerce_key_value(normalised)
    if extracted_again:
        key, value = extracted_again
        return {key: value}

    return normalised


def _normalise_modifications(raw: Any) -> Dict[str, Any]:
    """Normalise different modification payload shapes into a dict."""
    if raw is None:
        return {}

    if isinstance(raw, dict):
        return _normalise_mapping(raw)

    if isinstance(raw, str):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to decode modifications string; defaulting to empty dict")
            return {}
        return _normalise_modifications(decoded)

    if isinstance(raw, (list, tuple, set)):
        collected: Dict[str, Any] = {}
        iterable: Iterable[Any] = list(raw)
        for entry in iterable:
            if isinstance(entry, dict):
                for key, value in _normalise_mapping(entry).items():
                    collected[key] = value
            elif isinstance(entry, (list, tuple)) and entry:
                key = entry[0]
                if key is None:
                    continue
                value = entry[1] if len(entry) > 1 else None
                collected[str(key)] = value
            else:
                continue
        return collected

    return {}


def tool_edit_cart_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Edit ANY property of a cart item in ONE call.

    This is the ONLY tool for editing cart items.
    Can change size, protein, salads, sauces, chips_size, anything.

    Examples:
    - editCartItem(0, {"chips_size": "large"})
    - editCartItem(0, {"size": "large", "sauces": ["garlic", "chili"]})
    - editCartItem(1, {"salads": []})
    """
    try:
        item_index = params.get('itemIndex')

        modifications = _normalise_modifications(params.get('modifications'))

        # Accept VAPI "properties" payloads in all supported shapes
        if not modifications:
            modifications = _normalise_modifications(params.get('properties'))

        # Some integrations send {"property": "size", "value": "large"}
        if not modifications and params.get('property') and 'value' in params:
            modifications = {str(params['property']): params['value']}

        if not modifications:
            # Fall back to treating any additional params as modifications
            fallback = {
                key: value
                for key, value in params.items()
                if key not in {"itemIndex", "modifications", "properties", "property", "value"}
            }
            modifications = _normalise_modifications(fallback)

        if item_index is None:
            return {"ok": False, "error": "itemIndex is required"}

        if modifications:
            aux_keys = set(_MOD_KEY_CANDIDATES) | set(_MOD_VALUE_CANDIDATES)
            cleaned = {}
            for key, value in modifications.items():
                if key in aux_keys and any(k not in aux_keys for k in modifications):
                    continue
                cleaned[key] = value
            modifications = cleaned

        if not modifications:
            return {"ok": False, "error": "modifications object is required"}

        cart = session_get('cart', [])

        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            return {"ok": False, "error": "itemIndex must be a number"}

        if item_index < 0 or item_index >= len(cart):
            return {"ok": False, "error": f"Invalid itemIndex. Cart has {len(cart)} items (0-{len(cart)-1})"}

        # Get the item
        item = cart[item_index]

        logger.info(f"Editing item {item_index}: {modifications}")

        # Apply ALL modifications
        for field, value in modifications.items():
            if field == "size":
                item["size"] = value
                name = item.get("name", "")
                if name:
                    updated = re.sub(r"^(Small|Large)", value.capitalize(), name, count=1)
                    item["name"] = updated
            elif field == "protein":
                item["protein"] = value
            elif field == "salads":
                item["salads"] = value if isinstance(value, list) else []
            elif field == "sauces":
                item["sauces"] = value if isinstance(value, list) else []
            elif field == "extras":
                item["extras"] = value if isinstance(value, list) else []
            elif field == "cheese":
                item["cheese"] = bool(value)
            elif field == "quantity":
                item["quantity"] = int(value) if value else 1
            elif field == "salt_type":
                item["salt_type"] = value
            elif field == "chips_size":
                # CRITICAL: Handle meal chips upgrade
                if item.get('is_combo'):
                    old_chips_size = item.get('chips_size', 'small')
                    new_chips_size = value

                    item['chips_size'] = new_chips_size

                    # Recalculate combo price
                    if "Small Kebab Meal" in item.get('name', ''):
                        if new_chips_size == "large":
                            item['price'] = 20.0
                            item['name'] = "Small Kebab Meal (Large Chips)"
                        else:
                            item['price'] = 17.0
                            item['name'] = "Small Kebab Meal"
                    elif "Large Kebab Meal" in item.get('name', ''):
                        if new_chips_size == "large":
                            item['price'] = 25.0
                            item['name'] = "Large Kebab Meal (Large Chips)"
                        else:
                            item['price'] = 22.0
                            item['name'] = "Large Kebab Meal"

                    logger.info(f"Updated chips from {old_chips_size} to {new_chips_size}, new price: ${item['price']}")
                else:
                    logger.warning(f"chips_size can only be modified on combo/meal items")
            else:
                # Unknown field - just set it
                item[field] = value

        # Recalculate price if needed
        if not item.get('is_combo'):
            item['price'] = calculate_price(item)

        # Update cart
        cart[item_index] = item
        session_set('cart', cart)
        session_set('cart_priced', False)

        logger.info(f"Item {item_index} updated successfully: {item}")

        return {
            "ok": True,
            "message": f"Updated item at index {item_index}",
            "updatedItem": item
        }

    except Exception as e:
        logger.error(f"Error editing cart item: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}

# Tool 8: priceCart
def tool_price_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate total price with breakdown"""
    try:
        cart = session_get('cart', [])

        if not cart:
            return {
                "ok": True,
                "subtotal": 0.0,
                "gst": 0.0,
                "total": 0.0,
                "message": "Cart is empty"
            }

        subtotal = 0.0

        for item in cart:
            item_price = item.get('price', 0.0)
            quantity = item.get('quantity', 1)
            subtotal += item_price * quantity

        gst = round(subtotal * 0.1, 2)  # 10% GST
        total = round(subtotal + gst, 2)

        session_set('cart_priced', True)
        session_set('last_subtotal', subtotal)
        session_set('last_gst', gst)
        session_set('last_total', total)

        return {
            "ok": True,
            "subtotal": round(subtotal, 2),
            "gst": gst,
            "total": total,
            "itemCount": len(cart),
            "message": f"Total: ${total:.2f} (includes ${gst:.2f} GST)"
        }

    except Exception as e:
        logger.error(f"Error pricing cart: {e}")
        return {"ok": False, "error": str(e)}

# Tool 9: convertItemsToMeals
def tool_convert_items_to_meals(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert kebabs in cart to meals (kebab + chips + drink)"""
    try:
        cart = session_get('cart', [])
        item_indices = params.get('itemIndices')
        drink_brand = params.get('drinkBrand', 'coke')
        chips_size = params.get('chipsSize', 'small')
        chips_salt = params.get('chipsSalt', 'chicken')

        # If no indices specified, convert ALL kebabs
        if item_indices is None:
            item_indices = [i for i, item in enumerate(cart) if item.get('category') == 'kebabs']

        if not item_indices:
            return {"ok": False, "error": "No items to convert"}

        converted_count = 0

        for idx in item_indices:
            if idx < 0 or idx >= len(cart):
                continue

            item = cart[idx]

            # Can only convert kebabs
            if item.get('category') != 'kebabs':
                continue

            # Skip if already a combo
            if item.get('is_combo'):
                continue

            # Convert to meal
            kebab_size = item.get('size', 'small')

            # Determine meal price
            if kebab_size == 'small':
                meal_price = 20.0 if chips_size == 'large' else 17.0
                meal_name = f"Small Kebab Meal{' (Large Chips)' if chips_size == 'large' else ''}"
            else:
                meal_price = 25.0 if chips_size == 'large' else 22.0
                meal_name = f"Large Kebab Meal{' (Large Chips)' if chips_size == 'large' else ''}"

            # Update item
            item['is_combo'] = True
            item['name'] = meal_name
            item['price'] = meal_price
            item['chips_size'] = chips_size
            item['chips_salt'] = chips_salt
            item['drink_brand'] = drink_brand

            cart[idx] = item
            converted_count += 1

        session_set('cart', cart)
        session_set('cart_priced', False)

        return {
            "ok": True,
            "message": f"Converted {converted_count} items to meals",
            "convertedCount": converted_count
        }

    except Exception as e:
        logger.error(f"Error converting to meals: {e}")
        return {"ok": False, "error": str(e)}

# Tool 10: getOrderSummary
def tool_get_order_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get human-readable order summary for review"""
    try:
        cart = session_get('cart', [])

        if not cart:
            return {
                "ok": True,
                "summary": "No items in cart",
                "total": 0.0
            }

        # Format items
        summary_lines = []
        for idx, item in enumerate(cart):
            summary_lines.append(format_cart_item(item, idx + 1))

        # Get pricing
        subtotal = session_get('last_subtotal', 0.0)
        gst = session_get('last_gst', 0.0)
        total = session_get('last_total', 0.0)

        # If not priced yet, calculate now
        if not session_get('cart_priced'):
            price_result = tool_price_cart({})
            subtotal = price_result.get('subtotal', 0.0)
            gst = price_result.get('gst', 0.0)
            total = price_result.get('total', 0.0)

        summary_lines.append("")
        summary_lines.append(f"Subtotal: ${subtotal:.2f}")
        summary_lines.append(f"GST: ${gst:.2f}")
        summary_lines.append(f"TOTAL: ${total:.2f}")

        summary_text = "\n".join(summary_lines)

        return {
            "ok": True,
            "summary": summary_text,
            "total": total,
            "itemCount": len(cart)
        }

    except Exception as e:
        logger.error(f"Error getting order summary: {e}")
        return {"ok": False, "error": str(e)}

# Tool 11: setPickupTime
def tool_set_pickup_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set custom pickup time when customer requests specific time"""
    try:
        requested_time = params.get('requestedTime', '')

        if not requested_time:
            return {"ok": False, "error": "requestedTime is required"}

        # Parse the time (simple implementation)
        # In production, use dateparser or similar
        requested_time_clean = requested_time.lower().strip()

        # Try to extract time
        pickup_time = None

        # Check for "in X minutes"
        if 'minute' in requested_time_clean:
            match = re.search(r'(\d+)\s*minute', requested_time_clean)
            if match:
                minutes = int(match.group(1))
                pickup_time = datetime.now() + timedelta(minutes=minutes)

        # Check for specific time like "6pm" or "18:00"
        elif 'pm' in requested_time_clean or 'am' in requested_time_clean:
            match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm)', requested_time_clean)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                meridiem = match.group(3)

                if meridiem == 'pm' and hour < 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0

                pickup_time = datetime.now().replace(hour=hour, minute=minute, second=0)

        if not pickup_time:
            return {"ok": False, "error": f"Couldn't parse time from '{requested_time}'"}

        ready_at_iso = pickup_time.isoformat()
        ready_at_formatted = pickup_time.strftime("%I:%M %p")

        session_set('ready_at', ready_at_iso)
        session_set('ready_at_formatted', ready_at_formatted)

        return {
            "ok": True,
            "readyAt": ready_at_formatted,
            "readyAtIso": ready_at_iso,
            "message": f"Pickup time set for {ready_at_formatted}"
        }

    except Exception as e:
        logger.error(f"Error setting pickup time: {e}")
        return {"ok": False, "error": str(e)}

# Tool 12: estimateReadyTime
def tool_estimate_ready_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate when order will be ready for pickup"""
    try:
        # Simple estimation: 15-20 minutes based on cart size
        cart = session_get('cart', [])

        base_time = 15  # minutes
        per_item_time = 2  # minutes per item

        total_minutes = base_time + (len(cart) * per_item_time)
        total_minutes = min(total_minutes, 30)  # Cap at 30 minutes

        ready_time = datetime.now() + timedelta(minutes=total_minutes)
        ready_at_iso = ready_time.isoformat()
        ready_at_formatted = ready_time.strftime("%I:%M %p")

        session_set('ready_at', ready_at_iso)
        session_set('ready_at_formatted', ready_at_formatted)

        return {
            "ok": True,
            "estimatedMinutes": total_minutes,
            "readyAt": ready_at_formatted,
            "readyAtIso": ready_at_iso,
            "message": f"Your order will be ready in about {total_minutes} minutes (around {ready_at_formatted})"
        }

    except Exception as e:
        logger.error(f"Error estimating ready time: {e}")
        return {"ok": False, "error": str(e)}

# Tool 13: createOrder
def tool_create_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create and save final order to database"""
    try:
        customer_name = params.get('customerName', '').strip()
        customer_phone = params.get('customerPhone', '').strip()
        notes = params.get('notes', '').strip()

        if not customer_name:
            return {"ok": False, "error": "customerName is required"}

        if not customer_phone:
            return {"ok": False, "error": "customerPhone is required"}

        cart = session_get('cart', [])

        if not cart:
            return {"ok": False, "error": "Cart is empty"}

        # Get pricing
        if not session_get('cart_priced'):
            tool_price_cart({})

        subtotal = session_get('last_subtotal', 0.0)
        gst = session_get('last_gst', 0.0)
        total = session_get('last_total', 0.0)

        # Get ready time
        ready_at_iso = session_get('ready_at', '')

        if not ready_at_iso:
            # Auto-estimate if not set
            estimate_result = tool_estimate_ready_time({})
            ready_at_iso = estimate_result.get('readyAtIso', '')

        # Generate order number
        today = datetime.now().strftime("%Y%m%d")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM orders WHERE order_number LIKE ?
        ''', (f"{today}-%",))

        count = cursor.fetchone()[0]
        order_number = f"{today}-{count + 1:03d}"

        # Save order
        cursor.execute('''
            INSERT INTO orders (
                order_number, customer_name, customer_phone,
                cart_json, subtotal, gst, total,
                ready_at, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_number, customer_name, customer_phone,
            json.dumps(cart), subtotal, gst, total,
            ready_at_iso, notes, 'pending'
        ))

        conn.commit()
        conn.close()

        logger.info(f"Order {order_number} created for {customer_name}")

        # Clear cart
        session_set('cart', [])
        session_set('cart_priced', False)

        return {
            "ok": True,
            "orderNumber": order_number,
            "total": total,
            "readyAt": session_get('ready_at_formatted', ''),
            "message": f"Order {order_number} confirmed! Total ${total:.2f}. Ready at {session_get('ready_at_formatted', '')}"
        }

    except Exception as e:
        logger.error(f"Error creating order: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}

# Tool 14: repeatLastOrder
def tool_repeat_last_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Copy customer's last order to cart"""
    try:
        phone_number = params.get('phoneNumber', '').strip()

        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        # Get last order from database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT cart_json, total
            FROM orders
            WHERE customer_phone = ?
            ORDER BY created_at DESC
            LIMIT 1
        ''', (phone_number,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            return {"ok": False, "error": "No previous orders found"}

        cart_json, last_total = result
        last_cart = json.loads(cart_json)

        # Set as current cart
        session_set('cart', last_cart)
        session_set('cart_priced', False)

        return {
            "ok": True,
            "message": f"Loaded your last order ({len(last_cart)} items, ${last_total:.2f})",
            "itemCount": len(last_cart),
            "lastTotal": last_total
        }

    except Exception as e:
        logger.error(f"Error repeating last order: {e}")
        return {"ok": False, "error": str(e)}

# Tool 15: endCall
def tool_end_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """End the phone call gracefully"""
    try:
        # Clean up session
        session_id = get_session_id()
        if session_id in SESSIONS:
            logger.info(f"Ending call for session {session_id}")

        return {
            "ok": True,
            "message": "Thank you for calling Kebabalab. Have a great day!"
        }

    except Exception as e:
        logger.error(f"Error ending call: {e}")
        return {"ok": False, "error": str(e)}

# ==================== TOOL REGISTRY ====================

TOOLS = {
    "checkOpen": tool_check_open,
    "getCallerSmartContext": tool_get_caller_smart_context,
    "quickAddItem": tool_quick_add_item,
    "addMultipleItemsToCart": tool_add_multiple_items_to_cart,
    "getCartState": tool_get_cart_state,
    "removeCartItem": tool_remove_cart_item,
    "editCartItem": tool_edit_cart_item,
    "priceCart": tool_price_cart,
    "convertItemsToMeals": tool_convert_items_to_meals,
    "getOrderSummary": tool_get_order_summary,
    "setPickupTime": tool_set_pickup_time,
    "estimateReadyTime": tool_estimate_ready_time,
    "createOrder": tool_create_order,
    "repeatLastOrder": tool_repeat_last_order,
    "endCall": tool_end_call,
}

# ==================== WEBHOOK ====================

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "server": "kebabalab-simplified",
        "tools": len(TOOLS),
        "sessions": len(SESSIONS)
    })

@app.post("/webhook")
def webhook():
    """Main webhook endpoint for VAPI"""
    try:
        data = request.get_json() or {}
        message = data.get('message', {})
        tool_calls = message.get('toolCalls', []) or []

        if not tool_calls:
            return jsonify({"error": "No tool calls provided"}), 400

        results = []

        for tool_call in tool_calls:
            function_data = tool_call.get('function', {})
            function_name = function_data.get('name', '')
            raw_arguments = function_data.get('arguments', {})
            tool_call_id = tool_call.get('id') or tool_call.get('toolCallId')

            if isinstance(raw_arguments, str):
                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode tool arguments string; defaulting to empty dict")
                    arguments = {}
            else:
                arguments = raw_arguments or {}

            if not function_name:
                logger.error("Tool call missing function name")
                results.append({
                    "toolCallId": tool_call_id,
                    "result": {"ok": False, "error": "No function specified"}
                })
                continue

            logger.info(f"Tool call: {function_name}({arguments})")

            tool_func = TOOLS.get(function_name)

            if not tool_func:
                logger.error(f"Unknown tool: {function_name}")
                results.append({
                    "toolCallId": tool_call_id,
                    "result": {"ok": False, "error": f"Unknown tool: {function_name}"}
                })
                continue

            try:
                result = tool_func(arguments)
            except Exception as tool_error:
                logger.error(f"Error executing tool {function_name}: {tool_error}", exc_info=True)
                result = {"ok": False, "error": str(tool_error)}

            logger.info(f"Tool result: {result}")

            results.append({
                "toolCallId": tool_call_id,
                "result": result
            })

        return jsonify({"results": results})

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# ==================== STARTUP ====================

if __name__ == "__main__":
    logger.info("="*50)
    logger.info("Kebabalab VAPI Server - SIMPLIFIED")
    logger.info("="*50)

    # Initialize
    init_database()
    load_menu()

    logger.info(f"Loaded {len(TOOLS)} tools:")
    for i, tool_name in enumerate(TOOLS.keys(), 1):
        logger.info(f"  {i}. {tool_name}")

    # Run server
    port = int(os.getenv('PORT', 8000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

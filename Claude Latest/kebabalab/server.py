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
import pytz

# Fuzzy string matching for typo tolerance
try:
    from rapidfuzz import fuzz, process
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False
    logger.warning("rapidfuzz not available, fuzzy matching disabled")
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

# Optional Twilio client for SMS notifications
try:  # pragma: no cover - optional dependency
    from twilio.rest import Client  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised only when Twilio isn't installed
    Client = None  # type: ignore

# ==================== CONFIGURATION ====================

app = Flask(__name__)

# CORS configuration - restrict to VAPI domains for security
allowed_origins_str = os.getenv('ALLOWED_ORIGINS', 'https://api.vapi.ai,https://vapi.ai')
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

CORS(app, resources={
    r"/webhook": {
        "origins": allowed_origins,
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    },
    r"/health": {
        "origins": "*",  # Health check can be public
        "methods": ["GET"]
    }
})

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

# Business constants
MENU_LINK_URL = os.getenv('MENU_LINK_URL', 'https://www.kebabalab.com.au/menu.html')
SHOP_NUMBER_DEFAULT = os.getenv('SHOP_ORDER_TO', '0423680596')
SHOP_NAME = os.getenv('SHOP_NAME', 'Kebabalab')
SHOP_ADDRESS = os.getenv('SHOP_ADDRESS', 'Melbourne')

# Timezone configuration
SHOP_TIMEZONE_STR = os.getenv('SHOP_TIMEZONE', 'Australia/Melbourne')
try:
    SHOP_TIMEZONE = pytz.timezone(SHOP_TIMEZONE_STR)
except pytz.exceptions.UnknownTimeZoneError:
    logger.warning(f"Unknown timezone '{SHOP_TIMEZONE_STR}', falling back to Australia/Melbourne")
    SHOP_TIMEZONE = pytz.timezone('Australia/Melbourne')

# Global menu
MENU = {}

# In-memory sessions (in production, use Redis)
SESSIONS = {}

# Session configuration
SESSION_TTL = int(os.getenv('SESSION_TTL', '1800'))  # 30 minutes default
MAX_SESSIONS = int(os.getenv('MAX_SESSIONS', '1000'))  # Max concurrent sessions
# Will be initialized after SHOP_TIMEZONE is set
LAST_CLEANUP = None
CLEANUP_INTERVAL = timedelta(minutes=5)  # Run cleanup every 5 minutes

# ==================== DATABASE ====================

class DatabaseConnection:
    """Context manager for database connections with automatic cleanup"""

    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Open database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path, timeout=10.0)
            self.conn.row_factory = sqlite3.Row  # Enable column access by name
            self.cursor = self.conn.cursor()
            return self.cursor
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close connection and handle errors"""
        if exc_type is not None:
            # Exception occurred, rollback transaction
            if self.conn:
                try:
                    self.conn.rollback()
                    logger.warning(f"Transaction rolled back due to: {exc_val}")
                except sqlite3.Error as e:
                    logger.error(f"Rollback error: {e}")
        else:
            # No exception, commit transaction
            if self.conn:
                try:
                    self.conn.commit()
                except sqlite3.Error as e:
                    logger.error(f"Commit error: {e}")
                    raise

        # Always close the connection
        if self.cursor:
            try:
                self.cursor.close()
            except sqlite3.Error:
                pass
        if self.conn:
            try:
                self.conn.close()
            except sqlite3.Error:
                pass

        # Don't suppress the exception
        return False

def init_database():
    """Initialize SQLite database for orders"""
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    with DatabaseConnection() as cursor:
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

def cleanup_expired_sessions():
    """Remove expired sessions to prevent memory leaks"""
    global LAST_CLEANUP
    now = get_current_time()

    # Initialize LAST_CLEANUP on first run
    if LAST_CLEANUP is None:
        LAST_CLEANUP = now
        return

    # Only run cleanup every CLEANUP_INTERVAL
    if now - LAST_CLEANUP < CLEANUP_INTERVAL:
        return

    LAST_CLEANUP = now
    expired = []

    for session_id, session_data in SESSIONS.items():
        if '_meta' in session_data:
            last_access = session_data['_meta'].get('last_access')
            if last_access and (now - last_access).total_seconds() > SESSION_TTL:
                expired.append(session_id)

    for session_id in expired:
        del SESSIONS[session_id]

    if expired:
        logger.info(f"Cleaned up {len(expired)} expired sessions")

def enforce_session_limits():
    """Enforce maximum session count by removing oldest sessions"""
    if len(SESSIONS) <= MAX_SESSIONS:
        return

    # Sort sessions by last access time
    sessions_by_access = []
    for session_id, session_data in SESSIONS.items():
        last_access = session_data.get('_meta', {}).get('last_access', datetime.min)
        sessions_by_access.append((session_id, last_access))

    sessions_by_access.sort(key=lambda x: x[1])

    # Remove oldest sessions to get under limit
    to_remove = len(SESSIONS) - MAX_SESSIONS
    for session_id, _ in sessions_by_access[:to_remove]:
        del SESSIONS[session_id]

    logger.warning(f"Session limit reached. Removed {to_remove} oldest sessions")

def session_get(key: str, default=None):
    """Get value from session with TTL tracking"""
    cleanup_expired_sessions()  # Periodic cleanup

    session_id = get_session_id()
    now = get_current_time()

    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            '_meta': {
                'created_at': now,
                'last_access': now
            }
        }
    else:
        # Update last access time
        if '_meta' not in SESSIONS[session_id]:
            SESSIONS[session_id]['_meta'] = {}
        SESSIONS[session_id]['_meta']['last_access'] = now

    return SESSIONS[session_id].get(key, default)

def session_set(key: str, value: Any):
    """Set value in session with TTL tracking"""
    cleanup_expired_sessions()  # Periodic cleanup
    enforce_session_limits()  # Enforce max sessions

    session_id = get_session_id()
    now = get_current_time()

    if session_id not in SESSIONS:
        SESSIONS[session_id] = {
            '_meta': {
                'created_at': now,
                'last_access': now
            }
        }
    else:
        # Update last access time
        if '_meta' not in SESSIONS[session_id]:
            SESSIONS[session_id]['_meta'] = {}
        SESSIONS[session_id]['_meta']['last_access'] = now

    SESSIONS[session_id][key] = value

def session_clear(session_id: Optional[str] = None):
    """Clear a specific session or current session"""
    if session_id is None:
        session_id = get_session_id()
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        logger.info(f"Session cleared: {session_id}")

# ==================== INPUT VALIDATION ====================

def sanitize_for_sms(text: str) -> str:
    """Sanitize text for SMS to prevent injection attacks"""
    if not text:
        return ""
    # Remove control characters and limit to printable ASCII + common punctuation
    sanitized = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', str(text))
    # Remove potential SMS command characters
    sanitized = sanitized.replace('\n', ' ').replace('\r', ' ')
    # Limit length
    return sanitized[:500].strip()

def validate_customer_name(name: str) -> Tuple[bool, str]:
    """Validate customer name"""
    if not name or not isinstance(name, str):
        return False, "Customer name is required"

    name = name.strip()

    if len(name) < 2:
        return False, "Customer name must be at least 2 characters"

    if len(name) > 100:
        return False, "Customer name must be less than 100 characters"

    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, "Customer name can only contain letters, spaces, hyphens and apostrophes"

    return True, name

def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """Validate Australian phone number"""
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required"

    # Normalize to digits only
    digits = re.sub(r'\D', '', phone)

    # Check valid Australian formats
    # 04XXXXXXXX (10 digits) or 614XXXXXXXX (11 digits with country code)
    if len(digits) == 10 and digits.startswith('04'):
        return True, digits
    elif len(digits) == 11 and digits.startswith('614'):
        return True, '0' + digits[2:]  # Convert to local format
    elif len(digits) == 11 and digits.startswith('610'):
        return True, '0' + digits[2:]  # Convert landline to local format
    else:
        return False, "Phone number must be a valid Australian number (e.g., 04XX XXX XXX)"

def validate_quantity(quantity: Any) -> Tuple[bool, int]:
    """Validate item quantity"""
    try:
        qty = int(quantity)
        if qty < 1:
            return False, 1
        if qty > 99:
            return False, 99
        return True, qty
    except (ValueError, TypeError):
        return False, 1

def validate_menu_item(category: str, item_name: str, size: Optional[str] = None) -> Tuple[bool, str]:
    """Validate that menu item exists"""
    if not MENU:
        return False, "Menu not loaded"

    if category not in MENU:
        return False, f"Category '{category}' not found in menu"

    category_items = MENU[category].get('items', {})
    if item_name not in category_items:
        return False, f"Item '{item_name}' not found in category '{category}'"

    # Validate size if provided
    if size:
        item_data = category_items[item_name]
        available_sizes = item_data.get('sizes', ['regular'])
        if size not in available_sizes:
            return False, f"Size '{size}' not available for '{item_name}'. Available sizes: {', '.join(available_sizes)}"

    return True, "Valid"

def validate_customization(text: str) -> Tuple[bool, str]:
    """Validate customization text"""
    if not text:
        return True, ""

    text = str(text).strip()

    if len(text) > 200:
        return False, "Customization text too long (max 200 characters)"

    # Sanitize for SMS/database
    sanitized = sanitize_for_sms(text)
    return True, sanitized

def validate_price(price: Any) -> Tuple[bool, float]:
    """Validate price value"""
    try:
        price_float = float(price)
        if price_float < 0:
            return False, 0.0
        if price_float > 10000:  # Sanity check - no order over $10k
            return False, 10000.0
        return True, round(price_float, 2)
    except (ValueError, TypeError):
        return False, 0.0

# ==================== HELPER FUNCTIONS ====================

def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    if not text:
        return ""
    return text.lower().strip()

def fuzzy_match(text: str, choices: List[str], threshold: int = 80) -> Optional[str]:
    """
    Find best fuzzy match for text in choices.
    Returns matched choice if confidence >= threshold, None otherwise.
    Examples:
    - fuzzy_match("chiken", ["chicken", "lamb"]) -> "chicken"
    - fuzzy_match("galic", ["garlic", "chilli"]) -> "garlic"
    """
    if not FUZZY_MATCHING_AVAILABLE or not text or not choices:
        return None

    text = normalize_text(text)
    # Extract word tokens from text for better matching
    words = text.split()

    best_match = None
    best_score = 0

    for word in words:
        if len(word) < 3:  # Skip very short words
            continue
        result = process.extractOne(word, choices, scorer=fuzz.ratio)
        if result and result[1] >= threshold:
            if result[1] > best_score:
                best_score = result[1]
                best_match = result[0]

    return best_match

def get_current_time() -> datetime:
    """Get current time in shop's timezone (timezone-aware)"""
    return datetime.now(SHOP_TIMEZONE)

def get_local_time(dt: Optional[datetime] = None) -> datetime:
    """Convert datetime to shop's timezone. If None, returns current time."""
    if dt is None:
        return get_current_time()
    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        dt = pytz.utc.localize(dt)
    return dt.astimezone(SHOP_TIMEZONE)


def _human_join(items: Iterable[str]) -> str:
    """Join words with commas for natural speech."""
    cleaned = [str(item).strip() for item in items if str(item).strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    return ", ".join(cleaned)


def _title_case_phrase(value: Optional[str]) -> str:
    if not value:
        return ""
    words = re.split(r"\s+", str(value).replace('_', ' ').strip())
    return " ".join(word.capitalize() for word in words if word)


def _format_time_for_display(dt: datetime) -> str:
    formatted = dt.strftime("%I:%M %p")
    return formatted.lstrip('0') if formatted.startswith('0') else formatted


def _format_pickup_phrase(dt: datetime, minutes_offset: Optional[int] = None) -> str:
    formatted = _format_time_for_display(dt)
    if minutes_offset is not None:
        return f"in {minutes_offset} minutes ({formatted})"
    return formatted


def _normalize_au_local(phone: str) -> str:
    digits = re.sub(r"\D+", "", str(phone or ""))
    if not digits:
        return str(phone or "").strip()
    if digits.startswith("61") and len(digits) == 11:
        return "0" + digits[2:]
    if digits.startswith("0") and len(digits) == 10:
        return digits
    return digits


def _au_to_e164(phone: str) -> str:
    digits = re.sub(r"\D+", "", str(phone or ""))
    if not digits:
        return str(phone or "")
    if digits.startswith("0") and len(digits) == 10:
        return "+61" + digits[1:]
    if digits.startswith("61") and len(digits) == 11:
        return "+" + digits
    if str(phone).startswith("+"):
        return str(phone)
    return str(phone)


def _get_twilio_client():  # pragma: no cover - optional runtime dependency
    if Client is None:
        return None, None
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM') or os.getenv('TWILIO_PHONE_NUMBER')
    if not all([account_sid, auth_token, from_number]):
        return None, None
    try:
        client = Client(account_sid, auth_token)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to initialise Twilio client: {exc}")
        return None, None
    return client, from_number


def _send_sms(phone: str, body: str) -> Tuple[bool, Optional[str]]:
    client, from_number = _get_twilio_client()
    if not client or not from_number:
        return False, "SMS not configured"
    try:
        client.messages.create(body=body, from_=from_number, to=_au_to_e164(phone))
        return True, None
    except Exception as exc:  # pragma: no cover - network dependant
        logger.error(f"Failed to send SMS to {phone}: {exc}")
        return False, str(exc)


def _format_item_for_sms(item: Dict) -> str:
    qty = item.get('quantity', 1)
    prefix = f"{qty}x " if qty and qty > 1 else ""
    size = _title_case_phrase(item.get('size'))
    protein = _title_case_phrase(item.get('protein'))
    category = _title_case_phrase(item.get('category')) or _title_case_phrase(item.get('name'))

    if item.get('category') == 'kebabs':
        base = f"{size} {protein} Kebab".strip()
        if item.get('is_combo'):
            chips_size = _title_case_phrase(item.get('chips_size') or 'small')
            drink = _title_case_phrase(item.get('drink_brand') or 'coke')
            base = f"{size} {protein} Kebab Meal ({chips_size} chips, {drink})".strip()
    elif item.get('category') == 'hsp':
        cheese_text = "with cheese" if item.get('cheese') else "no cheese"
        base = f"{size} {protein} HSP ({cheese_text})"
    else:
        base = item.get('name') or category

    salads = item.get('salads') or []
    sauces = item.get('sauces') or []
    extras = [e for e in (item.get('extras') or []) if e]

    lines = [f"{prefix}{base}".strip()]
    if salads:
        lines.append(f"  • Salads: {_human_join(_title_case_phrase(s) for s in salads)}")
    if sauces:
        lines.append(f"  • Sauces: {_human_join(_title_case_phrase(s) for s in sauces)}")
    if extras:
        lines.append(f"  • Extras: {_human_join(_title_case_phrase(e) for e in extras)}")

    return "\n".join(lines)


def _send_order_notifications(
    order_display_number: str,
    customer_name: str,
    customer_phone: str,
    cart: List[Dict],
    total: float,
    ready_phrase: str,
    send_customer_sms: bool = True,
):
    client, from_number = _get_twilio_client()
    if not client or not from_number:  # pragma: no cover - optional runtime dependency
        logger.warning("SMS notifications skipped - Twilio not configured")
        return

    cart_summary = "\n\n".join(_format_item_for_sms(item) for item in cart)

    if send_customer_sms:
        customer_message = (
            f"🥙 {SHOP_NAME.upper()} ORDER {order_display_number}\n\n"
            f"{cart_summary}\n\n"
            f"TOTAL: ${total:.2f}\n"
            f"Ready {ready_phrase}\n\n"
            f"Thank you, {customer_name}!"
        )
        success, error = _send_sms(customer_phone, customer_message)
        if not success:
            logger.error(f"Customer SMS failed: {error}")

    shop_number = SHOP_NUMBER_DEFAULT
    shop_message = (
        f"🔔 NEW ORDER {order_display_number}\n\n"
        f"Customer: {customer_name}\n"
        f"Phone: {customer_phone}\n"
        f"Pickup: {ready_phrase}\n\n"
        f"ORDER DETAILS:\n{cart_summary}\n\n"
        f"TOTAL: ${total:.2f}\n"
        f"Location: {SHOP_ADDRESS}"
    )
    success, error = _send_sms(shop_number, shop_message)
    if not success:
        logger.error(f"Shop SMS failed: {error}")

def parse_protein(text: str) -> Optional[str]:
    """Extract protein type from text with fuzzy matching for typo tolerance"""
    text = normalize_text(text)

    # Exact matches first
    if any(word in text for word in ['lamb', 'lamp']):
        return 'lamb'
    if any(word in text for word in ['chicken', 'chiken', 'chkn']):
        return 'chicken'
    if 'mix' in text or 'mixed' in text:
        return 'mixed'
    if 'falafel' in text or 'vegan' in text:
        return 'falafel'

    # Fuzzy match if available (handles typos like "chikn", "lamm", "chicen")
    protein_choices = ['chicken', 'lamb', 'mixed', 'falafel']
    match = fuzzy_match(text, protein_choices, threshold=75)
    if match:
        logger.info(f"Fuzzy matched protein '{text}' to '{match}'")
        return match

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
    """Extract salads from text with fuzzy matching for typo tolerance"""
    text = normalize_text(text)
    salads = []

    # Check for "no salad" first
    if any(phrase in text for phrase in ['no salad', 'without salad', 'hold salad']):
        return []

    salad_map = {
        'lettuce': ['lettuce', 'letuce', 'letus'],
        'tomato': ['tomato', 'tomatos', 'toma'],
        'onion': ['onion', 'onions', 'onin'],
        'pickles': ['pickle', 'pickles', 'pickel'],
        'olives': ['olive', 'olives', 'olivs']
    }

    # Exact matches first
    for salad, keywords in salad_map.items():
        if any(keyword in text for keyword in keywords):
            salads.append(salad)

    # Fuzzy match for typos if no exact matches found
    if not salads and FUZZY_MATCHING_AVAILABLE:
        all_salad_choices = list(salad_map.keys())
        words = text.split()
        for word in words:
            if len(word) >= 4:  # Only check words of reasonable length
                match = fuzzy_match(word, all_salad_choices, threshold=75)
                if match and match not in salads:
                    salads.append(match)
                    logger.info(f"Fuzzy matched salad '{word}' to '{match}'")

    return salads

def parse_sauces(text: str) -> List[str]:
    """Extract sauces from text with fuzzy matching for typo tolerance"""
    text = normalize_text(text)
    sauces = []

    # Check for "no sauce" first
    if any(phrase in text for phrase in ['no sauce', 'without sauce', 'hold sauce']):
        return []

    sauce_map = {
        'garlic': ['garlic', 'garlek', 'galic', 'garlick'],
        'chilli': ['chili', 'chilli', 'chilly', 'chili sauce'],
        'bbq': ['bbq', 'barbeque', 'barbecue'],
        'tomato': ['tomato sauce', 'ketchup', 'tomatoe'],
        'sweet chilli': ['sweet chilli', 'sweet chili', 'sweet chilly'],
        'mayo': ['mayo', 'aioli', 'mayonnaise'],
        'hummus': ['hummus', 'humus', 'hummous']
    }

    # Exact matches first
    for sauce, keywords in sauce_map.items():
        if any(keyword in text for keyword in keywords):
            if sauce not in sauces:
                sauces.append(sauce)

    # Fuzzy match for typos if no exact matches found
    if not sauces and FUZZY_MATCHING_AVAILABLE:
        all_sauce_choices = list(sauce_map.keys())
        words = text.split()
        for word in words:
            if len(word) >= 4:  # Only check words of reasonable length
                match = fuzzy_match(word, all_sauce_choices, threshold=75)
                if match and match not in sauces:
                    sauces.append(match)
                    logger.info(f"Fuzzy matched sauce '{word}' to '{match}'")

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
    """Format a cart item for natural order review."""
    qty = max(1, int(item.get('quantity', 1) or 1))
    qty_prefix = f"{qty}x " if qty > 1 else ""

    category = item.get('category')
    size = _title_case_phrase(item.get('size'))
    protein = _title_case_phrase(item.get('protein'))
    salads = [s.lower() for s in (item.get('salads') or [])]
    sauces = [s.lower() for s in (item.get('sauces') or [])]
    extras = [e.lower() for e in (item.get('extras') or [])]

    segments: List[str] = []

    if category == 'kebabs':
        base = f"{size} {protein} kebab".strip()
        if item.get('is_combo'):
            chips_size = _title_case_phrase(item.get('chips_size') or 'small')
            drink = _title_case_phrase(item.get('drink_brand') or 'coke')
            base = f"{size} {protein} kebab meal with {chips_size.lower()} chips and a {drink}"
        segments.append(base.strip())
        segments.append(
            f"salads: {_human_join(s.capitalize() for s in salads) if salads else 'none'}"
        )
        segments.append(
            f"sauces: {_human_join(s.capitalize() for s in sauces) if sauces else 'none'}"
        )
    elif category == 'hsp':
        cheese_flag = item.get('cheese') or ('cheese' in extras)
        cheese_text = 'yes' if cheese_flag else 'no'
        base = f"{size} {protein} HSP"
        segments.append(base.strip())
        segments.append(f"cheese: {cheese_text}")
        segments.append(
            f"sauces: {_human_join(s.capitalize() for s in sauces) if sauces else 'none'}"
        )
    elif category == 'chips':
        salt_type = item.get('salt_type') or item.get('salt')
        base = f"{size} chips".strip()
        if salt_type:
            base += f" with {salt_type} salt"
        segments.append(base)
    else:
        name = item.get('name') or category or 'Item'
        segments.append(_title_case_phrase(name))

    extras_filtered = [e for e in extras if e != 'cheese']
    if extras_filtered:
        segments.append(
            f"extras: {_human_join(e.capitalize() for e in extras_filtered)}"
        )

    price = calculate_price(item) * qty
    line = f"{index}. {qty_prefix}{' | '.join(segments)} - ${price:.2f}"
    return line.strip()

# ==================== TOOL IMPLEMENTATIONS ====================

# Tool 1: checkOpen
def tool_check_open(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check if shop is currently open (timezone-aware)"""
    try:
        now = get_current_time()
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
        with DatabaseConnection() as cursor:
            cursor.execute('''
                SELECT order_number, cart_json, total, created_at
                FROM orders
                WHERE customer_phone = ?
                ORDER BY created_at DESC
                LIMIT 5
            ''', (phone,))

            orders = cursor.fetchall()

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
                "error": f"I didn't understand '{description}'. Try saying something like 'large chicken kebab with lettuce and garlic sauce' or '2 cokes' or 'small chips'."
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

        total = round(subtotal, 2)
        gst = 0.0

        session_set('cart_priced', True)
        session_set('last_subtotal', subtotal)
        session_set('last_gst', gst)
        session_set('last_total', total)
        session_set('last_totals', {
            'subtotal': round(subtotal, 2),
            'gst': gst,
            'grand_total': total,
        })

        return {
            "ok": True,
            "subtotal": round(subtotal, 2),
            "gst": gst,
            "total": total,
            "itemCount": len(cart),
            "message": f"Total: ${total:.2f}"
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

        totals_snapshot = session_get('last_totals', {})
        total = totals_snapshot.get('grand_total')

        if total is None or not session_get('cart_priced'):
            price_result = tool_price_cart({})
            totals_snapshot = session_get('last_totals', {})
            total = price_result.get('total', totals_snapshot.get('grand_total', 0.0))

        summary_lines.append("")
        summary_lines.append(f"Total: ${float(total or 0.0):.2f}")

        summary_text = "\n".join(summary_lines)

        return {
            "ok": True,
            "summary": summary_text,
            "total": float(total or 0.0),
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

        requested_time_clean = requested_time.lower().strip()
        now = datetime.now()
        pickup_time = None
        minutes_offset: Optional[int] = None

        if 'minute' in requested_time_clean:
            match = re.search(r'(\d+)\s*minute', requested_time_clean)
            if match:
                minutes = int(match.group(1))
                if minutes < 10:
                    return {"ok": False, "error": "Pickup time must be at least 10 minutes from now"}
                minutes_offset = minutes
                pickup_time = now + timedelta(minutes=minutes)
        else:
            ampm_match = re.search(r'(\d+)(?::(\d+))?\s*(am|pm)', requested_time_clean)
            time_only_match = re.search(r'\b(\d{1,2})(?::(\d{2}))\b', requested_time_clean)

            if ampm_match:
                hour = int(ampm_match.group(1))
                minute = int(ampm_match.group(2)) if ampm_match.group(2) else 0
                meridiem = ampm_match.group(3)

                if meridiem == 'pm' and hour < 12:
                    hour += 12
                elif meridiem == 'am' and hour == 12:
                    hour = 0

                pickup_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            elif time_only_match:
                hour = int(time_only_match.group(1))
                minute = int(time_only_match.group(2)) if time_only_match.group(2) else 0
                if hour < 24 and minute < 60:
                    pickup_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if not pickup_time:
            return {"ok": False, "error": f"Couldn't parse time from '{requested_time}'"}

        if pickup_time <= now:
            pickup_time += timedelta(days=1)

        diff_minutes = int((pickup_time - now).total_seconds() // 60)
        if diff_minutes < 10:
            return {"ok": False, "error": "Pickup time must be at least 10 minutes from now"}

        ready_at_iso = pickup_time.isoformat()
        ready_at_formatted = _format_time_for_display(pickup_time)
        ready_phrase = _format_pickup_phrase(pickup_time, minutes_offset) if minutes_offset is not None else f"at {ready_at_formatted}"

        session_set('ready_at', ready_at_iso)
        session_set('ready_at_formatted', ready_at_formatted)
        session_set('ready_at_speech', ready_phrase)
        session_set('pickup_confirmed', True)
        session_set('pickup_method', 'customer')
        session_set('pickup_requested_text', requested_time)

        return {
            "ok": True,
            "readyAt": ready_at_formatted,
            "readyAtIso": ready_at_iso,
            "message": f"Pickup time set for {ready_phrase}",
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

        ready_time = get_current_time() + timedelta(minutes=total_minutes)
        ready_at_iso = ready_time.isoformat()
        ready_at_formatted = _format_time_for_display(ready_time)
        ready_phrase = f"in about {total_minutes} minutes ({ready_at_formatted})"

        session_set('ready_at', ready_at_iso)
        session_set('ready_at_formatted', ready_at_formatted)
        session_set('ready_at_speech', ready_phrase)
        session_set('pickup_confirmed', True)
        session_set('pickup_method', 'estimate')
        session_set('pickup_requested_text', f"asap ~{total_minutes}m")

        return {
            "ok": True,
            "estimatedMinutes": total_minutes,
            "readyAt": ready_at_formatted,
            "readyAtIso": ready_at_iso,
            "message": f"Your order will be ready {ready_phrase}"
        }

    except Exception as e:
        logger.error(f"Error estimating ready time: {e}")
        return {"ok": False, "error": str(e)}

# Tool 13: createOrder
def tool_create_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create and save final order to database"""
    try:
        # Validate and sanitize customer name
        customer_name_raw = params.get('customerName', '').strip()
        name_valid, name_result = validate_customer_name(customer_name_raw)
        if not name_valid:
            return {"ok": False, "error": name_result}
        customer_name = sanitize_for_sms(name_result)

        # Validate and normalize phone number
        customer_phone_raw = params.get('customerPhone', '').strip()
        phone_valid, phone_result = validate_phone_number(customer_phone_raw)
        if not phone_valid:
            return {"ok": False, "error": phone_result}
        customer_phone = phone_result

        # Validate and sanitize notes
        notes_raw = params.get('notes', '').strip()
        notes_valid, notes_result = validate_customization(notes_raw)
        if not notes_valid:
            return {"ok": False, "error": f"Notes validation failed: {notes_result}"}
        notes = notes_result

        send_sms_raw = params.get('sendSMS', True)

        cart = session_get('cart', [])

        if not cart:
            return {"ok": False, "error": "Cart is empty"}

        if not session_get('cart_priced'):
            tool_price_cart({})

        totals_snapshot = session_get('last_totals', {})
        subtotal = totals_snapshot.get('subtotal', session_get('last_subtotal', 0.0))
        total = totals_snapshot.get('grand_total', session_get('last_total', 0.0))
        gst = 0.0

        if not session_get('pickup_confirmed', False):
            return {
                "ok": False,
                "error": "Pickup time not confirmed. Ask the customer when they'd like it ready, then call setPickupTime or estimateReadyTime.",
            }

        ready_at_iso = session_get('ready_at', '')
        if not ready_at_iso:
            return {
                "ok": False,
                "error": "Pickup time missing. Call setPickupTime or estimateReadyTime before creating the order.",
            }

        ready_at_formatted = session_get('ready_at_formatted', '')
        ready_phrase = session_get('ready_at_speech', ready_at_formatted)
        if isinstance(send_sms_raw, str):
            send_sms_flag = send_sms_raw.strip().lower() not in {'false', '0', 'no'}
        else:
            send_sms_flag = bool(send_sms_raw)

        today = get_current_time().strftime("%Y%m%d")

        with DatabaseConnection() as cursor:
            cursor.execute(
                '''
                SELECT COUNT(*) FROM orders WHERE order_number LIKE ?
                ''',
                (f"{today}-%",),
            )

            count = cursor.fetchone()[0]
            order_number = f"{today}-{count + 1:03d}"
            display_order = f"#{count + 1:03d}"

            cursor.execute(
                '''
                INSERT INTO orders (
                    order_number, customer_name, customer_phone,
                    cart_json, subtotal, gst, total,
                    ready_at, notes, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    order_number,
                    customer_name,
                    customer_phone,
                    json.dumps(cart),
                    float(subtotal),
                    gst,
                    float(total),
                    ready_at_iso,
                    notes,
                    'pending',
                ),
            )

        logger.info(f"Order {order_number} created for {customer_name}")

        display_ready = ready_phrase or ready_at_formatted or 'soon'
        cart_snapshot = json.loads(json.dumps(cart))

        session_set('last_order_cart', cart_snapshot)
        session_set('last_order_total', float(total))
        session_set('last_order_display', display_order)
        session_set('last_ready_phrase', display_ready)
        session_set('last_customer_name', customer_name)
        session_set('last_customer_phone', customer_phone)

        try:
            _send_order_notifications(
                display_order,
                customer_name,
                customer_phone,
                cart,
                float(total),
                display_ready,
                send_sms_flag,
            )
        except Exception as notification_error:  # pragma: no cover - safety net
            logger.error(f"Failed to send SMS notifications: {notification_error}")

        session_set('cart', [])
        session_set('cart_priced', False)
        session_set('pickup_confirmed', False)

        return {
            "ok": True,
            "orderNumber": order_number,
            "displayOrderNumber": display_order,
            "total": float(total),
            "readyAt": ready_at_formatted,
            "message": f"Order {display_order} confirmed! Total ${float(total):.2f}, ready {display_ready}",
        }

    except Exception as e:
        logger.error(f"Error creating order: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}


def tool_send_menu_link(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send the digital menu link via SMS."""
    try:
        phone_number = params.get('phoneNumber', '').strip()

        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        message = (
            "🥙 KEBABALAB MENU\n\n"
            f"Check out our full menu: {MENU_LINK_URL}\n\n"
            f"Call or text us on {SHOP_NUMBER_DEFAULT} if you need a hand!"
        )

        success, error = _send_sms(phone_number, message)
        if not success:
            return {"ok": False, "error": error or "SMS not configured"}

        return {"ok": True, "message": "Menu link sent!", "menuUrl": MENU_LINK_URL}

    except Exception as e:
        logger.error(f"Error sending menu link: {e}")
        return {"ok": False, "error": str(e)}


def tool_send_receipt(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send the latest order receipt via SMS."""
    try:
        phone_number = params.get('phoneNumber', '').strip()

        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        cart_snapshot = session_get('last_order_cart') or session_get('cart', [])
        if not cart_snapshot:
            return {"ok": False, "error": "No recent order available to send"}

        total = session_get('last_order_total', session_get('last_total', 0.0))
        display_order = session_get('last_order_display', '').strip() or '#---'
        ready_phrase = session_get(
            'last_ready_phrase',
            session_get('ready_at_speech', session_get('ready_at_formatted', 'soon')),
        )
        customer_name = session_get('last_customer_name', '').strip() or 'Customer'

        cart_summary = "\n\n".join(_format_item_for_sms(item) for item in cart_snapshot)

        message = (
            f"🥙 {SHOP_NAME.upper()} RECEIPT {display_order}\n\n"
            f"{cart_summary}\n\n"
            f"TOTAL: ${float(total):.2f}\n"
            f"Ready {ready_phrase}\n\n"
            f"Thanks, {customer_name}!"
        )

        success, error = _send_sms(phone_number, message)
        if not success:
            return {"ok": False, "error": error or "SMS not configured"}

        return {"ok": True, "message": "Receipt sent!", "order": display_order}

    except Exception as e:
        logger.error(f"Error sending receipt: {e}")
        return {"ok": False, "error": str(e)}


# Tool 14: repeatLastOrder
def tool_repeat_last_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Copy customer's last order to cart"""
    try:
        phone_number = params.get('phoneNumber', '').strip()

        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        # Get last order from database
        with DatabaseConnection() as cursor:
            cursor.execute('''
                SELECT cart_json, total
                FROM orders
                WHERE customer_phone = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''', (phone_number,))

            result = cursor.fetchone()

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
    """End the phone call gracefully and clear session"""
    try:
        # Clean up session to free memory
        session_id = get_session_id()
        if session_id in SESSIONS:
            logger.info(f"Ending call and clearing session: {session_id}")
            session_clear(session_id)

        return {
            "ok": True,
            "message": "Thank you for calling Kebabalab. Have a great day!"
        }

    except Exception as e:
        logger.error(f"Error ending call: {e}")
        return {"ok": False, "error": "Failed to end call"}

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
    "sendMenuLink": tool_send_menu_link,
    "sendReceipt": tool_send_receipt,
    "repeatLastOrder": tool_repeat_last_order,
    "endCall": tool_end_call,
}

# ==================== WEBHOOK ====================

@app.get("/health")
def health_check():
    """Health check endpoint - minimal information for security"""
    return jsonify({
        "status": "healthy",
        "server": "kebabalab",
        "version": "2.0"
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

def main() -> None:
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


if __name__ == "__main__":
    main()

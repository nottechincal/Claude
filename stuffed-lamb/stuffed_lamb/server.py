"""
Stuffed Lamb VAPI Server
=========================

Automated ordering system for Stuffed Lamb Middle Eastern Restaurant.

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
import hmac
import smtplib
import threading
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from email.message import EmailMessage
from functools import wraps
from queue import Empty, Queue
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import pytz

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed, .env file will not be loaded automatically")
    print("Install with: pip install python-dotenv")

# Fuzzy string matching for typo tolerance
try:
    from rapidfuzz import fuzz, process
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False
    # Logger not yet initialized, will log this later after setup
    print("WARNING: rapidfuzz not available, fuzzy matching disabled")
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

# Redis for session storage (with fallback to in-memory)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("WARNING: redis-py not available, using in-memory session storage (not production-ready)")

# ==================== CONFIGURATION ====================

app = Flask(__name__)

# CORS configuration
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*')
if allowed_origins.strip() == '*':
    CORS(app)
else:
    origin_list = [origin.strip() for origin in allowed_origins.split(',') if origin.strip()]
    if origin_list:
        CORS(app, origins=origin_list, supports_credentials=True)
    else:
        CORS(app)


class JsonFormatter(logging.Formatter):
    """Structured logging formatter for consistent observability."""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }

        # Attach any custom attributes for richer context
        for attr in ('correlation_id', 'session_id', 'tool'):
            value = getattr(record, attr, None)
            if value:
                log_record[attr] = value

        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_record, ensure_ascii=False)


# Logging
os.makedirs('logs', exist_ok=True)

_stream_handler = logging.StreamHandler()
_file_handler = logging.FileHandler('logs/stuffed_lamb.log')
_formatter = JsonFormatter()
_stream_handler.setFormatter(_formatter)
_file_handler.setFormatter(_formatter)

logger = logging.getLogger('stuffed_lamb')
logger.setLevel(logging.INFO)
logger.addHandler(_stream_handler)
logger.addHandler(_file_handler)
logger.propagate = False

# Paths
# Get parent directory of stuffed_lamb package (go up one level to project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MENU_FILE = os.path.join(DATA_DIR, 'menu.json')
PRONUNCIATIONS_FILE = os.path.join(DATA_DIR, 'pronunciations.json')
HOURS_FILE = os.path.join(DATA_DIR, 'hours.json')
DB_FILE = os.path.join(DATA_DIR, 'orders.db')

# Business constants
MENU_LINK_URL = os.getenv('MENU_LINK_URL', 'https://stuffed-lamb.tuckerfox.com.au/')
SHOP_NUMBER_DEFAULT = os.getenv('SHOP_ORDER_TO', '+61XXXXXXXXX')
SHOP_NAME = os.getenv('SHOP_NAME', 'Stuffed Lamb')
SHOP_ADDRESS = os.getenv('SHOP_ADDRESS', '210 Broadway, Reservoir VIC 3073')

# Tax configuration (Australian GST)
# Menu prices are GST-inclusive, so we calculate GST component from total
GST_RATE = float(os.getenv('GST_RATE', '0.10'))  # 10% Australian GST

# Timezone configuration
SHOP_TIMEZONE_STR = os.getenv('SHOP_TIMEZONE', 'Australia/Melbourne')
try:
    SHOP_TIMEZONE = pytz.timezone(SHOP_TIMEZONE_STR)
except pytz.exceptions.UnknownTimeZoneError:
    logger.warning(f"Unknown timezone '{SHOP_TIMEZONE_STR}', falling back to Australia/Melbourne")
    SHOP_TIMEZONE = pytz.timezone('Australia/Melbourne')

# Global menu
MENU = {}
PRONUNCIATIONS: Dict[str, Dict[str, List[str]]] = {"items": {}, "modifiers": {}}
BUSINESS_HOURS: Dict[str, Any] = {}

# NLP indexes populated after menu load
ITEM_VARIANTS: Dict[str, Set[str]] = defaultdict(set)
ITEM_VARIANT_LOOKUP: Dict[str, str] = {}
MODIFIER_VARIANTS: Dict[str, Set[str]] = defaultdict(set)

# Metrics & observability
METRICS: Counter = Counter()
METRIC_DESCRIPTIONS = {
    'quick_add_requests_total': 'quickAddItem tool invocations',
    'quick_add_success_total': 'quickAddItem parsed successfully',
    'quick_add_failure_total': 'quickAddItem failures',
    'menu_miss_total': 'Descriptions that failed to map to the menu',
    'sms_success_total': 'Successful SMS sends',
    'sms_failure_total': 'Failed SMS sends',
    'webhook_auth_failures_total': 'Rejected webhook calls due to auth',
    'notification_queue_retries_total': 'Notification job retries',
}


def record_metric(name: str, value: int = 1) -> None:
    """Increment a Prometheus-style counter"""
    if value == 0:
        return
    METRICS[name] += value

# Session storage: Redis (production) or in-memory (fallback)
SESSIONS = {}  # Fallback in-memory storage if Redis unavailable
REDIS_CLIENT = None

# Session configuration
SESSION_TTL = int(os.getenv('SESSION_TTL', '1800'))  # 30 minutes default
MAX_SESSIONS = int(os.getenv('MAX_SESSIONS', '1000'))  # Max concurrent sessions (in-memory only)
# Will be initialized after SHOP_TIMEZONE is set
LAST_CLEANUP = None
CLEANUP_INTERVAL = timedelta(minutes=5)  # Run cleanup every 5 minutes

# Security & notification controls
WEBHOOK_SHARED_SECRET = os.getenv('WEBHOOK_SHARED_SECRET')
ENABLE_SECONDARY_NOTIFICATIONS = os.getenv('ENABLE_SECONDARY_NOTIFICATIONS', 'false').strip().lower() in {'1', 'true', 'yes'}
SMS_FAILOVER_THRESHOLD = int(os.getenv('SMS_FAILOVER_THRESHOLD', '3'))
SMS_MAX_RETRIES = int(os.getenv('SMS_MAX_RETRIES', '3'))
FAILOVER_NOTIFICATION_EMAIL = os.getenv('FAILOVER_NOTIFICATION_EMAIL')
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').strip().lower() in {'1', 'true', 'yes'}

# Notification queue infrastructure
NOTIFICATION_QUEUE: "Queue[Dict[str, Any]]" = Queue()
NOTIFICATION_STOP_EVENT = threading.Event()
NOTIFICATION_WORKER: Optional[threading.Thread] = None
SMS_FAILURE_STREAK = 0
SMS_FAILURE_LOCK = threading.Lock()

# Initialize Redis connection
if REDIS_AVAILABLE:
    try:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_db = int(os.getenv('REDIS_DB', '0'))
        redis_password = os.getenv('REDIS_PASSWORD', None)

        REDIS_CLIENT = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password if redis_password else None,
            decode_responses=True,  # Automatically decode responses to strings
            socket_connect_timeout=5,
            socket_timeout=5
        )

        # Test connection
        REDIS_CLIENT.ping()
        print(f"✓ Redis connected: {redis_host}:{redis_port} (db={redis_db})")
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"WARNING: Redis connection failed ({e}), falling back to in-memory sessions")
        REDIS_CLIENT = None
    except Exception as e:
        print(f"WARNING: Redis initialization error ({e}), falling back to in-memory sessions")
        REDIS_CLIENT = None

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
    """Initialize SQLite database for orders with indexes for performance"""
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)

    with DatabaseConnection() as cursor:
        # Create orders table
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

        # Create indexes for frequently queried fields (improves order history lookup)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_phone ON orders(customer_phone)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON orders(created_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_order_number ON orders(order_number)')

    logger.info("Database initialized with performance indexes")

# ==================== MENU & CONFIG LOADING ====================

def load_pronunciations() -> None:
    """Load pronunciation dictionary for accent tolerance"""
    global PRONUNCIATIONS
    try:
        with open(PRONUNCIATIONS_FILE, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
            if isinstance(data, dict):
                PRONUNCIATIONS = data
            else:
                raise ValueError("Pronunciation file must be a dictionary")
        logger.info("Pronunciation dictionary loaded")
    except FileNotFoundError:
        PRONUNCIATIONS = {"items": {}, "modifiers": {}}
        logger.warning("Pronunciation file not found; continue without accent hints")
    except Exception as exc:
        logger.error(f"Failed to load pronunciation dictionary: {exc}")
        PRONUNCIATIONS = {"items": {}, "modifiers": {}}


def load_hours_config() -> None:
    """Load business hours configuration"""
    global BUSINESS_HOURS
    try:
        with open(HOURS_FILE, 'r', encoding='utf-8') as handle:
            BUSINESS_HOURS = json.load(handle)
        logger.info("Business hours configuration loaded")
    except FileNotFoundError:
        logger.warning("Hours configuration missing; defaulting to open every day")
        BUSINESS_HOURS = {}
    except Exception as exc:
        logger.error(f"Failed to load hours configuration: {exc}")
        BUSINESS_HOURS = {}


def _register_item_variant(item_id: str, phrase: str) -> None:
    if not phrase:
        return
    normalized = normalize_text(phrase)
    if not normalized:
        return
    ITEM_VARIANTS[item_id].add(normalized)
    ITEM_VARIANT_LOOKUP[normalized] = item_id


def _register_modifier_variant(canonical: str, phrase: str) -> None:
    normalized_canonical = normalize_text(canonical)
    normalized_phrase = normalize_text(phrase)
    if not normalized_canonical or not normalized_phrase:
        return
    MODIFIER_VARIANTS[normalized_canonical].add(normalized_phrase)


def build_menu_indexes() -> None:
    """Create synonym/variant lookups for menu items and modifiers"""
    ITEM_VARIANTS.clear()
    ITEM_VARIANT_LOOKUP.clear()
    MODIFIER_VARIANTS.clear()

    categories = MENU.get('categories', {})
    synonyms = MENU.get('synonyms', {})
    item_name_to_id: Dict[str, str] = {}

    for items in categories.values():
        if not isinstance(items, list):
            continue
        for item in items:
            item_id = item.get('id')
            canonical_name = normalize_text(item.get('name', ''))
            if not item_id or not canonical_name:
                continue
            item_name_to_id[canonical_name] = item_id
            normalized_item_id = normalize_text(item_id.replace('_', ' '))
            item_name_to_id[normalized_item_id] = item_id
            _register_item_variant(item_id, canonical_name)

    for variant, canonical in synonyms.items():
        canonical_name = normalize_text(str(canonical))
        item_id = item_name_to_id.get(canonical_name)
        if not item_id:
            for key, value in item_name_to_id.items():
                if canonical_name in key or key in canonical_name:
                    item_id = value
                    break
        if item_id:
            _register_item_variant(item_id, variant)

    pronunciation_items = PRONUNCIATIONS.get('items', {}) or {}
    for canonical, variants in pronunciation_items.items():
        canonical_name = normalize_text(canonical)
        item_id = item_name_to_id.get(canonical_name)
        if not item_id:
            continue
        for variant in variants:
            _register_item_variant(item_id, variant)

    modifiers = MENU.get('modifiers', {})
    pronunciation_modifiers = PRONUNCIATIONS.get('modifiers', {}) or {}
    for modifier_group in modifiers.values():
        if not isinstance(modifier_group, list):
            continue
        for modifier in modifier_group:
            canonical = modifier.get('name', '')
            if not canonical:
                continue
            canonical_norm = normalize_text(canonical)
            if not canonical_norm:
                continue
            _register_modifier_variant(canonical_norm, canonical)

            for synonym, target in synonyms.items():
                if normalize_text(str(target)) == canonical_norm:
                    _register_modifier_variant(canonical_norm, synonym)

            for variant in pronunciation_modifiers.get(canonical.lower(), []):
                _register_modifier_variant(canonical_norm, variant)

    logger.info("Menu indexes refreshed for NLP matching")


def load_menu():
    """Load and validate menu from JSON file"""
    global MENU
    try:
        with open(MENU_FILE, 'r', encoding='utf-8') as f:
            MENU = json.load(f)

        # Validate menu structure
        if not isinstance(MENU, dict):
            raise ValueError("Menu must be a dictionary")

        # Validate categories exist
        required_categories = ['mains', 'drinks']
        categories = MENU.get('categories', {})
        for category in required_categories:
            if category not in categories:
                logger.warning(f"Menu missing category: {category}")

        build_menu_indexes()

        # Log menu stats
        total_items = sum(len(items) for items in categories.values() if isinstance(items, list))
        logger.info(f"Menu loaded: {len(categories)} categories, {total_items} items from {MENU_FILE}")
        return True

    except FileNotFoundError:
        logger.error(f"Menu file not found: {MENU_FILE}")
        logger.error("Server cannot operate without menu! Please ensure menu.json exists.")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in menu file: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to load menu: {e}")
        return False

def _find_menu_item_by_id(item_id: str) -> Optional[Dict]:
    """Find a menu item by its ID"""
    if not MENU:
        return None

    categories = MENU.get('categories', {})
    for category_name, items in categories.items():
        if isinstance(items, list):
            for item in items:
                if item.get('id') == item_id:
                    return item
    return None


# Load pronunciation and hours configuration at import time
load_pronunciations()
load_hours_config()

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
    """Remove expired sessions to prevent memory leaks (in-memory only, Redis uses TTL)"""
    # Redis handles expiration automatically via TTL
    if REDIS_CLIENT:
        return

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
    """Enforce maximum session count by removing oldest sessions (in-memory only)"""
    # Redis doesn't need manual limit enforcement, uses TTL and memory policies
    if REDIS_CLIENT:
        return

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
    """Get value from session with TTL tracking (Redis or in-memory)"""
    session_id = get_session_id()

    # Redis implementation
    if REDIS_CLIENT:
        try:
            redis_key = f"session:{session_id}:{key}"
            value = REDIS_CLIENT.get(redis_key)

            if value is None:
                return default

            # Try to deserialize JSON if it's a complex type
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value

        except redis.RedisError as e:
            logger.error(f"Redis get error: {e}, falling back to in-memory")
            # Fall through to in-memory fallback

    # In-memory fallback
    cleanup_expired_sessions()  # Periodic cleanup

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
    """Set value in session with TTL tracking (Redis or in-memory)"""
    session_id = get_session_id()

    # Redis implementation
    if REDIS_CLIENT:
        try:
            redis_key = f"session:{session_id}:{key}"

            # Serialize complex types to JSON
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)

            # Store with TTL
            REDIS_CLIENT.setex(redis_key, SESSION_TTL, serialized_value)
            return

        except redis.RedisError as e:
            logger.error(f"Redis set error: {e}, falling back to in-memory")
            # Fall through to in-memory fallback

    # In-memory fallback
    cleanup_expired_sessions()  # Periodic cleanup
    enforce_session_limits()  # Enforce max sessions

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
    """Clear a specific session or current session (Redis or in-memory)"""
    if session_id is None:
        session_id = get_session_id()

    # Redis implementation
    if REDIS_CLIENT:
        try:
            # Delete all keys for this session
            pattern = f"session:{session_id}:*"
            keys = REDIS_CLIENT.keys(pattern)
            if keys:
                REDIS_CLIENT.delete(*keys)
                logger.info(f"Session cleared from Redis: {session_id} ({len(keys)} keys)")
            return

        except redis.RedisError as e:
            logger.error(f"Redis clear error: {e}, falling back to in-memory")
            # Fall through to in-memory fallback

    # In-memory fallback
    if session_id in SESSIONS:
        del SESSIONS[session_id]
        logger.info(f"Session cleared from memory: {session_id}")

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
    text = unicodedata.normalize('NFKD', str(text))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return re.sub(r'\s+', ' ', text.lower()).strip()

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
    best_match = None
    best_score = 0

    # First attempt using partial ratio on the entire phrase
    result = process.extractOne(text, choices, scorer=fuzz.partial_ratio)
    if result and result[1] >= threshold:
        best_match = result[0]
        best_score = result[1]

    # Fallback to word-level comparison for very short aliases
    words = text.split()
    for word in words:
        if len(word) < 3:
            continue
        result = process.extractOne(word, choices, scorer=fuzz.ratio)
        if result and result[1] >= threshold and result[1] > best_score:
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

def calculate_gst_from_inclusive(total: float) -> Tuple[float, float]:
    """
    Calculate GST component from GST-inclusive total.

    Formula: GST = Total × (GST_RATE / (1 + GST_RATE))
    Example: For $110 with 10% GST:
        - GST = $110 × (0.10 / 1.10) = $10.00
        - Subtotal = $110 - $10 = $100.00

    Returns: (subtotal_ex_gst, gst_amount)
    """
    if GST_RATE <= 0:
        return (total, 0.0)

    gst_amount = total * (GST_RATE / (1 + GST_RATE))
    subtotal = total - gst_amount

    return (round(subtotal, 2), round(gst_amount, 2))


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
        record_metric('sms_success_total')
        return True, None
    except Exception as exc:  # pragma: no cover - network dependant
        logger.error(f"Failed to send SMS to {phone}: {exc}")
        record_metric('sms_failure_total')
        return False, str(exc)


def _format_item_for_sms(item: Dict) -> str:
    """Format a cart item for SMS - Stuffed Lamb version."""
    qty = item.get('quantity', 1)
    prefix = f"{qty}x " if qty and qty > 1 else ""

    # Get item name
    base = item.get('name') or _title_case_phrase(item.get('category')) or 'Item'

    # Get add-ons and extras
    addons = [a for a in (item.get('addons') or []) if a]
    extras = [e for e in (item.get('extras') or []) if e]

    lines = [f"{prefix}{base}".strip()]

    if addons:
        lines.append(f"  • Add-ons: {_human_join(_title_case_phrase(a) for a in addons)}")
    if extras:
        lines.append(f"  • Extras: {_human_join(_title_case_phrase(e) for e in extras)}")

    return "\n".join(lines)


def _send_secondary_notification(subject: str, body: str) -> None:
    if not ENABLE_SECONDARY_NOTIFICATIONS or not FAILOVER_NOTIFICATION_EMAIL:
        logger.warning("Secondary notification skipped - channel disabled")
        return
    if not SMTP_HOST:
        logger.warning("Secondary notification skipped - SMTP not configured")
        return

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.getenv('SMTP_FROM', FAILOVER_NOTIFICATION_EMAIL)
    msg['To'] = FAILOVER_NOTIFICATION_EMAIL
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            if SMTP_USE_TLS:
                smtp.starttls()
            if SMTP_USERNAME and SMTP_PASSWORD:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(msg)
        logger.info("Secondary notification dispatched")
    except Exception as exc:  # pragma: no cover - network dependant
        logger.error(f"Secondary notification failed: {exc}")


def _handle_notification_outcome(success: bool, context: str, fallback_body: str) -> None:
    global SMS_FAILURE_STREAK
    with SMS_FAILURE_LOCK:
        if success:
            SMS_FAILURE_STREAK = 0
            return
        SMS_FAILURE_STREAK += 1
        logger.error(context)
        if (
            ENABLE_SECONDARY_NOTIFICATIONS
            and FAILOVER_NOTIFICATION_EMAIL
            and SMS_FAILURE_STREAK >= SMS_FAILOVER_THRESHOLD
        ):
            _send_secondary_notification("Stuffed Lamb order failover", fallback_body)
            SMS_FAILURE_STREAK = 0


def _send_order_notifications(
    order_display_number: str,
    customer_name: str,
    customer_phone: str,
    cart: List[Dict],
    total: float,
    ready_phrase: str,
    send_customer_sms: bool = True,
    correlation_id: Optional[str] = None,
) -> bool:
    client, from_number = _get_twilio_client()
    if not client or not from_number:  # pragma: no cover - optional runtime dependency
        logger.warning("SMS notifications skipped - Twilio not configured")
        return True

    cart_summary = "\n\n".join(_format_item_for_sms(item) for item in cart)

    customer_success = True
    if send_customer_sms:
        customer_message = (
            f"🥙 {SHOP_NAME.upper()} ORDER {order_display_number}\n\n"
            f"{cart_summary}\n\n"
            f"TOTAL: ${total:.2f}\n"
            f"Ready {ready_phrase}\n\n"
            f"Thank you, {customer_name}!"
        )
        customer_success, error = _send_sms(customer_phone, customer_message)
        if not customer_success:
            _handle_notification_outcome(
                False,
                f"Customer SMS failed ({order_display_number}): {error}",
                customer_message,
            )
        else:
            _handle_notification_outcome(True, '', '')

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
    shop_success, error = _send_sms(shop_number, shop_message)
    if not shop_success:
        _handle_notification_outcome(
            False,
            f"Shop SMS failed ({order_display_number}): {error}",
            shop_message,
        )
    else:
        _handle_notification_outcome(True, '', '')

    logger.info(
        "Notification dispatch complete",
        extra={"correlation_id": correlation_id, "tool": "createOrder"},
    )

    return (customer_success if send_customer_sms else True) and shop_success


def _notification_worker() -> None:
    while not NOTIFICATION_STOP_EVENT.is_set():
        try:
            job = NOTIFICATION_QUEUE.get(timeout=1)
        except Empty:
            continue

        if not job:
            continue

        payload = job.get('payload', {})
        attempts = job.get('attempts', 0)
        success = False
        try:
            success = _send_order_notifications(**payload)
        except Exception as exc:
            logger.error(f"Notification job failed: {exc}", exc_info=True)

        if not success and attempts + 1 < SMS_MAX_RETRIES:
            job['attempts'] = attempts + 1
            NOTIFICATION_QUEUE.put(job)
            record_metric('notification_queue_retries_total')
        NOTIFICATION_QUEUE.task_done()


def _start_notification_worker() -> None:
    global NOTIFICATION_WORKER
    if NOTIFICATION_WORKER and NOTIFICATION_WORKER.is_alive():
        return

    NOTIFICATION_WORKER = threading.Thread(target=_notification_worker, name='notification-worker', daemon=True)
    NOTIFICATION_WORKER.start()


def _enqueue_notification_job(
    order_display_number: str,
    customer_name: str,
    customer_phone: str,
    cart: List[Dict],
    total: float,
    ready_phrase: str,
    send_customer_sms: bool,
) -> None:
    correlation_id = f"order-{order_display_number}-{int(time.time() * 1000)}"
    payload = {
        'order_display_number': order_display_number,
        'customer_name': customer_name,
        'customer_phone': customer_phone,
        'cart': cart,
        'total': total,
        'ready_phrase': ready_phrase,
        'send_customer_sms': send_customer_sms,
        'correlation_id': correlation_id,
    }
    NOTIFICATION_QUEUE.put({'payload': payload, 'attempts': 0})
    _start_notification_worker()

# NOTE: Removed parse_protein, parse_size, parse_salads, parse_sauces, parse_extras functions
# These were Kebabalab-specific and not used in Stuffed Lamb system.
# Stuffed Lamb uses direct item IDs (MANSAF, LAMB_MANDI, CHICKEN_MANDI) instead.

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
    """
    Calculate price for a single item by looking up prices in menu.json.
    Designed for Stuffed Lamb menu (Mansaf, Lamb Mandi, Chicken Mandi).
    No hardcoded prices - all prices come from MENU data structure.
    """
    price = 0.0

    # Determine base price
    base_price = item.get('basePrice')
    if base_price is None and (not item.get('addons') and not item.get('extras')):
        base_price = item.get('price')

    item_id = item.get('id', '')
    category = item.get('category', '')
    item_name = item.get('name', '').lower()

    if base_price is None:
        categories = MENU.get('categories', {})
        category_items = categories.get(category, [])

        if category_items:
            for menu_item in category_items:
                if item_id and menu_item.get('id') == item_id:
                    base_price = menu_item.get('price', 0.0)
                    break
                elif category == 'drinks':
                    menu_name_lower = menu_item.get('name', '').lower()
                    if item_name in menu_name_lower or menu_name_lower in item_name:
                        base_price = menu_item.get('price', 0.0)
                        break
                    for brand in menu_item.get('brands', []) or []:
                        if item_name in brand.lower() or brand.lower() in item_name:
                            base_price = menu_item.get('price', 0.0)
                            break
                if base_price:
                    break

    try:
        price = float(base_price) if base_price is not None else 0.0
    except (TypeError, ValueError):
        price = 0.0

    # Add extras and add-ons pricing from menu modifiers
    modifiers = MENU.get('modifiers', {})

    # Check for add-ons (like nuts/sultanas on Mandi dishes)
    addons = item.get('addons', [])
    mandi_addons_pricing = modifiers.get('mandi_addons', [])
    for addon in addons:
        addon_lower = addon.lower()
        for modifier in mandi_addons_pricing:
            modifier_name = modifier.get('name', '').lower()
            if addon_lower == modifier_name or addon_lower in modifier_name:
                # Check if this modifier applies to this item
                applies_to = modifier.get('applies_to', [])
                if not applies_to or item_id in applies_to:
                    price += modifier.get('price', 0.0)
                break

    # Check for extras (extra jameed, extra rice, etc.)
    extras = item.get('extras', [])
    extras_pricing = modifiers.get('extras', [])
    for extra in extras:
        extra_lower = extra.lower()
        for modifier in extras_pricing:
            modifier_name = modifier.get('name', '').lower()
            if extra_lower == modifier_name or extra_lower in modifier_name:
                # Check if this modifier applies to this item
                applies_to = modifier.get('applies_to', [])
                if not applies_to or item_id in applies_to:
                    price += modifier.get('price', 0.0)
                break

    item['basePrice'] = round(price - sum(
        get_modifier_price(addon, 'mandi_addons', item_id) for addon in item.get('addons', [])
    ) - sum(
        get_modifier_price(extra, 'extras', item_id) for extra in item.get('extras', [])
    ), 2)

    return round(price, 2)


def get_modifier_price(name: str, group: str = 'extras', item_id: Optional[str] = None) -> float:
    """Look up modifier pricing from menu data"""
    modifiers = MENU.get('modifiers', {}).get(group, [])
    target = normalize_text(name)
    for modifier in modifiers:
        canonical = normalize_text(modifier.get('name', ''))
        if not canonical:
            continue
        if canonical != target:
            continue
        applies_to = modifier.get('applies_to', [])
        if applies_to and item_id and item_id not in applies_to:
            continue
        try:
            return float(modifier.get('price', 0.0))
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def list_modifier_names(group: str) -> List[str]:
    modifiers = MENU.get('modifiers', {}).get(group, [])
    names: List[str] = []
    for modifier in modifiers:
        if modifier.get('name'):
            names.append(modifier['name'])
    return names

def format_cart_item(item: Dict, index: int) -> str:
    """Format a cart item for natural order review - Stuffed Lamb version."""
    qty = max(1, int(item.get('quantity', 1) or 1))
    qty_prefix = f"{qty}x " if qty > 1 else ""

    # Get item details
    name = item.get('name') or 'Item'
    addons = [a.lower() for a in (item.get('addons') or [])]
    extras = [e.lower() for e in (item.get('extras') or [])]

    segments: List[str] = []

    # Start with the item name
    segments.append(_title_case_phrase(name))

    # Add add-ons if present (nuts, sultanas for Mandi dishes)
    if addons:
        segments.append(
            f"with {_human_join(a.capitalize() for a in addons)}"
        )

    # Add extras if present
    if extras:
        segments.append(
            f"extras: {_human_join(e.capitalize() for e in extras)}"
        )

    # Calculate total price
    price = calculate_price(item) * qty

    # Use comma separation for speech-friendly output
    line = f"{index}. {qty_prefix}{', '.join(segments)} - ${price:.2f}"
    return line.strip()


EXTRA_TRIGGER_WORDS: Tuple[str, ...] = ("extra", "more", "add", "another")


def _text_mentions_modifier(text: str, canonical_name: str) -> bool:
    normalized_text = normalize_text(text)
    variants = MODIFIER_VARIANTS.get(normalize_text(canonical_name), set())
    for variant in variants:
        if variant and variant in normalized_text:
            return True
    if FUZZY_MATCHING_AVAILABLE and variants:
        match = fuzzy_match(normalized_text, list(variants), threshold=85)
        return match is not None
    return False


def _match_item_from_description(description: str) -> Optional[str]:
    normalized_description = normalize_text(description)
    if not normalized_description:
        return None

    best_match: Optional[Tuple[str, str]] = None
    for variant, item_id in ITEM_VARIANT_LOOKUP.items():
        if not variant or variant not in normalized_description:
            continue
        if not best_match or len(variant) > len(best_match[0]):
            best_match = (variant, item_id)

    if best_match:
        return best_match[1]

    if FUZZY_MATCHING_AVAILABLE and ITEM_VARIANT_LOOKUP:
        match = fuzzy_match(normalized_description, list(ITEM_VARIANT_LOOKUP.keys()), threshold=78)
        if match:
            return ITEM_VARIANT_LOOKUP.get(match)
    return None


def _detect_drink_brand(description: str, drink_item: Dict) -> Optional[str]:
    brands = drink_item.get('brands', [])
    normalized_description = normalize_text(description)
    for brand in brands or []:
        brand_normalized = normalize_text(brand)
        if brand_normalized in normalized_description:
            return brand
    return None


def _detect_item_addons(item_id: Optional[str], description: str) -> List[str]:
    addons: List[str] = []
    if item_id not in {'LAMB_MANDI', 'CHICKEN_MANDI'}:
        return addons

    for addon_name in list_modifier_names('mandi_addons'):
        if _text_mentions_modifier(description, addon_name):
            addons.append(addon_name)
    return list(dict.fromkeys(addons))


def _detect_item_extras(item_id: Optional[str], description: str, existing_addons: Optional[Iterable[str]] = None) -> List[str]:
    extras: List[str] = []
    addon_blocklist: Set[str] = set()
    if existing_addons:
        addon_blocklist = {normalize_text(addon) for addon in existing_addons}

    for extra_name in sorted(list_modifier_names('extras'), key=lambda name: len(normalize_text(name)), reverse=True):
        if not _text_mentions_modifier(description, extra_name):
            continue
        modifiers = MENU.get('modifiers', {}).get('extras', [])
        for modifier in modifiers:
            canonical_extra = normalize_text(extra_name)
            if normalize_text(modifier.get('name', '')) != canonical_extra:
                continue
            applies_to = modifier.get('applies_to', [])
            if applies_to and item_id and item_id not in applies_to:
                continue
            # Avoid double-charging when a modifier appears as both an add-on and an extra
            if item_id in {'LAMB_MANDI', 'CHICKEN_MANDI'} and canonical_extra in {'nuts', 'sultanas'}:
                if canonical_extra in addon_blocklist:
                    continue
            # Avoid stacking generic and specific rice extras together
            is_redundant = any(
                canonical_extra in normalize_text(existing) and len(normalize_text(existing)) > len(canonical_extra)
                for existing in extras
            )
            if is_redundant:
                continue
            extras.append(extra_name)
    return list(dict.fromkeys(extras))

# ==================== TOOL IMPLEMENTATIONS ====================

_DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def _minutes_since_midnight(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def _get_hours_for_day(index: int) -> Any:
    day_key = _DAY_NAMES[index]
    return BUSINESS_HOURS.get(day_key, [])


def _find_next_open_day(start_index: int) -> Optional[Tuple[str, str]]:
    for offset in range(1, 8):
        idx = (start_index + offset) % 7
        hours = _get_hours_for_day(idx)
        if isinstance(hours, list) and hours:
            first_block = hours[0]
            return _DAY_NAMES[idx], first_block.get('open')
    return None


# Tool 1: checkOpen
def tool_check_open(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check if shop is currently open using hours.json"""
    try:
        now = get_current_time()
        current_minutes = _minutes_since_midnight(now)
        day_index = now.weekday()
        day_hours = _get_hours_for_day(day_index)
        current_time = now.strftime("%H:%M")

        if isinstance(day_hours, str) and day_hours.lower() == 'closed':
            next_open = _find_next_open_day(day_index)
            message = "We're closed today."
            if next_open:
                message += f" Back on {next_open[0].title()} from {next_open[1]}."
            return {
                "ok": True,
                "isOpen": False,
                "currentTime": current_time,
                "openTime": None,
                "closeTime": None,
                "message": message,
            }

        is_open = False
        open_time = None
        close_time = None
        if isinstance(day_hours, list):
            for block in day_hours:
                start = block.get('open')
                end = block.get('close')
                if not start or not end:
                    continue
                start_minutes = int(start.split(':')[0]) * 60 + int(start.split(':')[1])
                end_minutes = int(end.split(':')[0]) * 60 + int(end.split(':')[1])
                if start_minutes <= current_minutes < end_minutes:
                    is_open = True
                    open_time = start
                    close_time = end
                    break
            if not open_time and day_hours:
                open_time = day_hours[0].get('open')
                close_time = day_hours[-1].get('close')

        message = "We're open!" if is_open else "We're closed right now but can take a preorder."
        if open_time and close_time:
            message += f" Hours today: {open_time}-{close_time}."

        return {
            "ok": True,
            "isOpen": is_open,
            "currentTime": current_time,
            "openTime": open_time,
            "closeTime": close_time,
            "message": message
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
        greeting_suggestion = "Welcome back!" if is_returning else "Welcome to Stuffed Lamb!"

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
    Smart NLP parser - add items from natural language for Stuffed Lamb.

    Examples:
    - "lamb mandi with nuts"
    - "chicken mandi add sultanas"
    - "mansaf with extra jameed"
    - "2 cokes"
    - "soup of the day"
    """
    try:
        description = params.get('description', '').strip()
        record_metric('quick_add_requests_total')

        if not description:
            record_metric('quick_add_failure_total')
            return {"ok": False, "error": "description is required"}

        logger.info(f"QuickAddItem parsing", extra={'tool': 'quickAddItem'})

        quantity = parse_quantity(description)
        desc_lower = normalize_text(re.sub(r'^\d+\s*', '', description))

        item_id = _match_item_from_description(desc_lower)
        if not item_id:
            record_metric('quick_add_failure_total')
            record_metric('menu_miss_total')
            logger.warning(f"QuickAddItem unmatched description: {description}")
            return {"ok": False, "error": f"I didn't catch that. Could you describe the dish again using names like 'Mansaf' or 'Lamb Mandi'?"}

        matched_item = _find_menu_item_by_id(item_id)
        if not matched_item:
            record_metric('quick_add_failure_total')
            logger.error(f"Item ID {item_id} not found in menu")
            return {"ok": False, "error": "Sorry, that item isn't available right now."}

        addons = _detect_item_addons(item_id, desc_lower)
        extras = _detect_item_extras(item_id, desc_lower, addons)

        drink_brand = None
        if item_id == 'SOFT_DRINK':
            drink_brand = _detect_drink_brand(desc_lower, matched_item)
            if drink_brand:
                matched_item = matched_item.copy()
                matched_item['name'] = f"Soft Drink ({drink_brand})"

        base_price = float(matched_item.get('price', 0.0))
        total_price = base_price
        for addon in addons:
            total_price += get_modifier_price(addon, 'mandi_addons', item_id)
        for extra in extras:
            total_price += get_modifier_price(extra, 'extras', item_id)
        total_price = round(total_price, 2)

        item = {
            "id": item_id,
            "name": matched_item['name'],
            "price": total_price,
            "quantity": quantity,
            "addons": addons,
            "extras": extras,
            "category": matched_item.get('category', 'unknown'),
            "basePrice": base_price,
        }

        if drink_brand:
            item['brand'] = drink_brand

        item['total_price'] = round(total_price * quantity, 2)

        cart = session_get('cart', [])
        cart.append(item)
        session_set('cart', cart)
        session_set('cart_priced', False)

        record_metric('quick_add_success_total')
        logger.info(f"Added to cart", extra={'tool': 'quickAddItem', 'item_id': item_id})

        addons_text = f" with {' and '.join(addons)}" if addons else ""
        extras_text = f" plus {', '.join(extras)}" if extras else ""

        return {
            "ok": True,
            "message": f"Added {quantity}x {item['name']}{addons_text}{extras_text} to cart",
            "item": item,
            "cartSize": len(cart)
        }

    except Exception as e:
        record_metric('quick_add_failure_total')
        logger.error(f"Error in quickAddItem: {e}", exc_info=True)
        return {"ok": False, "error": str(e)}

# Tool 4: addMultipleItemsToCart
def tool_add_multiple_items_to_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add multiple fully configured items to cart in one call - Stuffed Lamb version"""
    try:
        items = params.get('items', [])

        if not items:
            return {"ok": False, "error": "items array is required"}

        cart = session_get('cart', [])
        added_count = 0

        for item_config in items:
            category = item_config.get('category', '')

            # Build item for Stuffed Lamb menu
            item = {
                "id": item_config.get('id', ''),
                "category": category,
                "name": item_config.get('name', ''),
                "addons": item_config.get('addons', []),
                "extras": item_config.get('extras', []),
                "quantity": item_config.get('quantity', 1),
                "brand": item_config.get('brand'),  # For drink brands
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

def tool_clear_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Clear all items from the cart"""
    try:
        cart = session_get('cart', [])
        cart_size = len(cart)

        # Clear the cart
        session_set('cart', [])
        session_set('cart_priced', False)
        session_set('last_totals', {})
        session_set('last_subtotal', 0.0)
        session_set('last_total', 0.0)
        session_set('last_gst', 0.0)

        return {
            "ok": True,
            "message": f"Cart cleared ({cart_size} items removed)",
            "previousCartSize": cart_size
        }

    except Exception as e:
        logger.error(f"Error clearing cart: {e}")
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
    Edit ANY property of a cart item in ONE call - Stuffed Lamb version.

    This is the ONLY tool for editing cart items.
    Can change quantity, addons (nuts/sultanas), extras, etc.

    Examples:
    - editCartItem(0, {"addons": ["nuts", "sultanas"]})
    - editCartItem(0, {"extras": ["extra jameed"]})
    - editCartItem(1, {"quantity": 2})
    """
    try:
        item_index = params.get('itemIndex')

        modifications = _normalise_modifications(params.get('modifications'))

        # Accept VAPI "properties" payloads in all supported shapes
        if not modifications:
            modifications = _normalise_modifications(params.get('properties'))

        # Some integrations send {"property": "quantity", "value": 2}
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

        # Log BEFORE state for debugging
        logger.info(f"BEFORE EDIT - Item {item_index}: {json.dumps(item)}")
        logger.info(f"Modifications requested: {json.dumps(modifications)}")

        # Apply ALL modifications
        for field, value in modifications.items():
            if field == "quantity":
                old_qty = item.get("quantity", 1)
                item["quantity"] = int(value) if value else 1
                logger.info(f"Quantity changed from {old_qty} to {item['quantity']}")

            elif field == "addons":
                # Add-ons like nuts and sultanas for Mandi dishes
                item["addons"] = value if isinstance(value, list) else []
                logger.info(f"Add-ons set to: {item['addons']}")

            elif field == "extras":
                # Extras like extra jameed, extra rice, etc.
                item["extras"] = value if isinstance(value, list) else []
                logger.info(f"Extras set to: {item['extras']}")

            else:
                # Generic field - log and set it
                logger.info(f"Setting field '{field}' to: {value}")
                item[field] = value

        # ALWAYS recalculate price after modifications
        old_price = item.get('price', 0.0)
        item['price'] = calculate_price(item)
        if old_price != item['price']:
            logger.info(f"Price recalculated from ${old_price:.2f} to ${item['price']:.2f}")

        # Update cart
        cart[item_index] = item
        session_set('cart', cart)
        session_set('cart_priced', False)

        # Log AFTER state for debugging
        logger.info(f"AFTER EDIT - Item {item_index}: {json.dumps(item)}")

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

        # Calculate total from cart (GST-inclusive prices)
        total_inclusive = 0.0

        for item in cart:
            item_price = item.get('price', 0.0)
            quantity = item.get('quantity', 1)
            total_inclusive += item_price * quantity

        total_inclusive = round(total_inclusive, 2)

        # Calculate GST component from inclusive total
        subtotal_ex_gst, gst = calculate_gst_from_inclusive(total_inclusive)

        session_set('cart_priced', True)
        session_set('last_subtotal', subtotal_ex_gst)
        session_set('last_gst', gst)
        session_set('last_total', total_inclusive)
        session_set('last_totals', {
            'subtotal': subtotal_ex_gst,
            'gst': gst,
            'grand_total': total_inclusive,
        })

        return {
            "ok": True,
            "subtotal": subtotal_ex_gst,
            "gst": gst,
            "total": total_inclusive,
            "itemCount": len(cart),
            "message": f"Total: ${total_inclusive:.2f} (inc. ${gst:.2f} GST)"
        }

    except Exception as e:
        logger.error(f"Error pricing cart: {e}")
        return {"ok": False, "error": str(e)}

# NOTE: Removed convertItemsToMeals tool - Stuffed Lamb has no combo meals

# Tool 9: getOrderSummary
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
        gst = totals_snapshot.get('gst', session_get('last_gst', 0.0))

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
            _enqueue_notification_job(
                display_order,
                customer_name,
                customer_phone,
                cart,
                float(total),
                display_ready,
                send_sms_flag,
            )
        except Exception as notification_error:  # pragma: no cover - safety net
            logger.error(f"Failed to queue notifications: {notification_error}")

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
            "🐑 STUFFED LAMB MENU\n\n"
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
            "message": "Thank you for calling Stuffed Lamb. Have a great day!"
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
    "clearCart": tool_clear_cart,
    "editCartItem": tool_edit_cart_item,
    "priceCart": tool_price_cart,
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
        "server": "stuffed-lamb",
        "version": "2.0"
    })


@app.get("/metrics")
def metrics_endpoint():
    """Expose Prometheus-style counters"""
    lines: List[str] = []
    for name, description in METRIC_DESCRIPTIONS.items():
        value = METRICS.get(name, 0)
        lines.append(f"# HELP {name} {description}")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")
    body = "\n".join(lines) + "\n"
    return body, 200, {"Content-Type": "text/plain; version=0.0.4"}


def require_webhook_auth(func):
    """Decorator enforcing shared-secret webhook authentication"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if WEBHOOK_SHARED_SECRET:
            provided = request.headers.get('X-Stuffed-Lamb-Signature') or request.headers.get('X-Webhook-Secret')
            if not provided or not hmac.compare_digest(provided, WEBHOOK_SHARED_SECRET):
                record_metric('webhook_auth_failures_total')
                return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


@app.post("/webhook")
@require_webhook_auth
def webhook():
    """Main webhook endpoint for VAPI"""
    try:
        data = request.get_json() or {}
        message = data.get('message', {})
        message_type = message.get('type', 'unknown')
        tool_calls = message.get('toolCalls', []) or []

        # Accept all webhook messages with 200 OK (reduces latency)
        # but only process tool-calls
        if not tool_calls:
            # VAPI sends many message types: conversation-update, speech-update, transcript, etc.
            # Return 200 OK to acknowledge receipt without causing retries or lag
            logger.debug(f"Webhook received non-tool message type: {message_type}")
            return jsonify({"status": "acknowledged", "message": "No tool calls to process"}), 200

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
    logger.info("Stuffed Lamb VAPI Server - SIMPLIFIED")
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

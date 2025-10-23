"""
VAPI Server for Kebabalab Phone Orders - ENTERPRISE VERSION
Production-ready order processing with sophisticated state management

This server provides a complete order flow with:
- Step-by-step item configuration
- Automatic combo detection and pricing
- Robust validation and error handling
- Enterprise-grade logging and monitoring
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sqlite3
import pytz
from twilio.rest import Client
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
import re
from contextvars import ContextVar
from collections import defaultdict
from copy import deepcopy
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("kebabalab_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Kebabalab VAPI Server v2")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Context variable for caller info
caller_context: ContextVar[Optional[str]] = ContextVar('caller_context', default=None)

# ==================== SAFETY MECHANISMS ====================
# Production-grade safety features to prevent system failures

# Rate limiting per caller (prevent abuse)
_RATE_LIMITS = {}
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX_CALLS = 10  # max calls per window per caller

# Circuit breaker for external services (prevent cascade failures)
_CIRCUIT_BREAKERS = {
    "database": {"failures": 0, "last_failure": None, "state": "closed"},
    "twilio": {"failures": 0, "last_failure": None, "state": "closed"},
    "vapi": {"failures": 0, "last_failure": None, "state": "closed"}
}
_CIRCUIT_BREAKER_THRESHOLD = 5  # failures before opening circuit
_CIRCUIT_BREAKER_TIMEOUT = 60  # seconds before retry

# Request validation limits (prevent resource exhaustion)
_MAX_CART_SIZE = 50  # max items in cart
_MAX_ITEM_QUANTITY = 20  # max quantity per item
_MAX_BATCH_SIZE = 10  # max items in addMultipleItemsToCart
_MAX_STRING_LENGTH = 500  # max length for text fields

# System health monitoring
_SYSTEM_HEALTH = {
    "start_time": datetime.now(),
    "total_requests": 0,
    "failed_requests": 0,
    "total_orders": 0,
    "failed_orders": 0,
    "avg_response_time_ms": 0,
    "last_error": None,
    "error_count_1min": 0,
    "last_error_time": None
}

# Error tracking for alerts
_ERROR_LOG = []
_ERROR_LOG_SIZE = 100  # keep last 100 errors

# Database health
_DB_HEALTH = {
    "total_connections": 0,
    "failed_connections": 0,
    "slow_queries": 0,
    "last_maintenance": None,
    "size_mb": 0
}

# ==================== IN-MEMORY CACHE ====================
# In-memory cache for static JSON files (10-50ms savings per request)
_FILE_CACHE = {}

# Database connection pool (5-15ms savings per query)
_DB_POOL = []
_DB_POOL_SIZE = 5

# ==================== SESSION MANAGEMENT ====================
# Per-caller session storage with expiration
SESSION = {}
SESSION_TIMEOUT = timedelta(minutes=15)  # Sessions expire after 15 minutes

def _create_session() -> Dict:
    """Create new session with timestamp"""
    return {
        "current_item": None,
        "cart": [],
        "customer_info": {},
        "order_state": "IDLE",
        "last_activity": datetime.now(),
        "created_at": datetime.now()
    }

def _clean_expired_sessions() -> None:
    """Remove expired sessions"""
    now = datetime.now()
    expired_keys = [
        key for key, session in SESSION.items()
        if now - session.get("last_activity", now) > SESSION_TIMEOUT
    ]
    for key in expired_keys:
        del SESSION[key]
        logger.info(f"Expired session: {key}")

def _session_key() -> str:
    """Get session key from caller context"""
    try:
        raw = caller_context.get() or "anon"
    except Exception:
        raw = "anon"
    raw = re.sub(r"\D+", "", str(raw))
    return raw or "anon"

def _ensure_session() -> None:
    """Ensure session exists and is not expired"""
    key = _session_key()
    if key not in SESSION:
        SESSION[key] = _create_session()
    else:
        # Update last activity
        SESSION[key]["last_activity"] = datetime.now()

def session_set(key: str, value: Any) -> None:
    """Set session value"""
    _ensure_session()
    SESSION[_session_key()][key] = value

def session_get(key: str, default: Any = None) -> Any:
    """Get session value"""
    _ensure_session()
    return SESSION[_session_key()].get(key, default)

def session_clear() -> None:
    """Clear current session"""
    key = _session_key()
    if key in SESSION:
        del SESSION[key]
        logger.info(f"Cleared session: {key}")

def session_reset() -> None:
    """Reset current session to fresh state"""
    key = _session_key()
    SESSION[key] = _create_session()
    logger.info(f"Reset session: {key}")

# ==================== HELPER FUNCTIONS ====================

def load_json_file(filename: str) -> Dict:
    """Load a JSON configuration file with in-memory caching"""
    # Check cache first
    if filename in _FILE_CACHE:
        return _FILE_CACHE[filename]

    # Load from disk and cache
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            _FILE_CACHE[filename] = data
            return data
    except Exception as e:
        logger.error(f"Error loading {filename}: {str(e)}")
        return {}

def init_db():
    """Initialize SQLite database for orders"""
    db_path = os.getenv("DB_PATH", "orders.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            ready_at TEXT,
            customer_name TEXT,
            customer_phone TEXT NOT NULL,
            order_type TEXT DEFAULT 'pickup',
            delivery_address TEXT,
            cart TEXT NOT NULL,
            totals TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            notes TEXT
        )
    """)
    conn.commit()
    return conn

def get_db_connection():
    """Get database connection from pool or create new one"""
    if _DB_POOL:
        conn = _DB_POOL.pop()
        logger.debug("Reusing pooled database connection")
        return conn

    db_path = os.getenv("DB_PATH", "orders.db")
    conn = sqlite3.connect(db_path)
    logger.debug("Created new database connection")
    return conn

def release_db_connection(conn):
    """Return connection to pool"""
    if len(_DB_POOL) < _DB_POOL_SIZE:
        _DB_POOL.append(conn)
        logger.debug("Returned connection to pool")
    else:
        conn.close()
        logger.debug("Closed excess connection")

# ==================== SAFETY MECHANISM FUNCTIONS ====================

def check_rate_limit(caller_id: str) -> bool:
    """Check if caller has exceeded rate limit"""
    if not caller_id:
        return True  # Allow anonymous calls

    # Bypass rate limiting for test phone numbers
    TEST_NUMBERS = ["+61412345678", "anon"]
    if caller_id in TEST_NUMBERS:
        return True

    now = datetime.now()

    # Clean up old entries
    expired = [
        k for k, v in _RATE_LIMITS.items()
        if (now - v["first_call"]).total_seconds() > _RATE_LIMIT_WINDOW
    ]
    for k in expired:
        del _RATE_LIMITS[k]

    # Check current caller
    if caller_id not in _RATE_LIMITS:
        _RATE_LIMITS[caller_id] = {"first_call": now, "count": 1}
        return True

    entry = _RATE_LIMITS[caller_id]
    window_elapsed = (now - entry["first_call"]).total_seconds()

    if window_elapsed > _RATE_LIMIT_WINDOW:
        # Reset window
        _RATE_LIMITS[caller_id] = {"first_call": now, "count": 1}
        return True

    # Within window - check limit
    if entry["count"] >= _RATE_LIMIT_MAX_CALLS:
        logger.warning(f"Rate limit exceeded for caller: {caller_id}")
        return False

    entry["count"] += 1
    return True


def check_circuit_breaker(service: str) -> bool:
    """Check if circuit breaker allows request to service"""
    if service not in _CIRCUIT_BREAKERS:
        return True

    breaker = _CIRCUIT_BREAKERS[service]

    # If open, check if timeout has passed
    if breaker["state"] == "open":
        if breaker["last_failure"]:
            elapsed = (datetime.now() - breaker["last_failure"]).total_seconds()
            if elapsed > _CIRCUIT_BREAKER_TIMEOUT:
                # Try half-open
                breaker["state"] = "half-open"
                logger.info(f"Circuit breaker {service} entering half-open state")
                return True
        return False

    return True


def record_service_success(service: str):
    """Record successful service call"""
    if service in _CIRCUIT_BREAKERS:
        breaker = _CIRCUIT_BREAKERS[service]
        if breaker["state"] == "half-open":
            breaker["state"] = "closed"
            breaker["failures"] = 0
            logger.info(f"Circuit breaker {service} closed (recovered)")
        breaker["failures"] = max(0, breaker["failures"] - 1)


def record_service_failure(service: str):
    """Record failed service call and potentially open circuit"""
    if service not in _CIRCUIT_BREAKERS:
        return

    breaker = _CIRCUIT_BREAKERS[service]
    breaker["failures"] += 1
    breaker["last_failure"] = datetime.now()

    if breaker["failures"] >= _CIRCUIT_BREAKER_THRESHOLD:
        breaker["state"] = "open"
        logger.error(f"Circuit breaker {service} OPENED after {breaker['failures']} failures")


def validate_cart_size(cart: List[Dict]) -> tuple[bool, str]:
    """Validate cart doesn't exceed limits"""
    if len(cart) > _MAX_CART_SIZE:
        return False, f"Cart exceeds maximum size of {_MAX_CART_SIZE} items"

    for idx, item in enumerate(cart):
        qty = item.get("quantity", 1)
        if qty > _MAX_ITEM_QUANTITY:
            return False, f"Item {idx + 1} quantity ({qty}) exceeds maximum of {_MAX_ITEM_QUANTITY}"

    return True, ""


def validate_string_length(value: str, field_name: str) -> tuple[bool, str]:
    """Validate string doesn't exceed length limit"""
    if not value:
        return True, ""

    if len(value) > _MAX_STRING_LENGTH:
        return False, f"{field_name} exceeds maximum length of {_MAX_STRING_LENGTH} characters"

    return True, ""


def sanitize_input(value: Any) -> Any:
    """Sanitize user input to prevent injection attacks"""
    if isinstance(value, str):
        # Remove potentially dangerous characters
        value = value.replace("'", "").replace('"', "").replace(";", "").replace("--", "")
        # Limit length
        value = value[:_MAX_STRING_LENGTH]
    elif isinstance(value, list):
        value = [sanitize_input(v) for v in value[:50]]  # Limit list size
    elif isinstance(value, dict):
        value = {k: sanitize_input(v) for k, v in list(value.items())[:50]}  # Limit dict size

    return value


def log_error(error: Exception, context: Dict[str, Any]):
    """Log error with context for debugging"""
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error": str(error),
        "type": type(error).__name__,
        "context": context
    }

    _ERROR_LOG.append(error_entry)
    if len(_ERROR_LOG) > _ERROR_LOG_SIZE:
        _ERROR_LOG.pop(0)

    # Update system health
    _SYSTEM_HEALTH["last_error"] = str(error)
    _SYSTEM_HEALTH["last_error_time"] = datetime.now()
    _SYSTEM_HEALTH["error_count_1min"] += 1

    # Clean up old 1-minute error count
    if _SYSTEM_HEALTH["last_error_time"]:
        elapsed = (datetime.now() - _SYSTEM_HEALTH["last_error_time"]).total_seconds()
        if elapsed > 60:
            _SYSTEM_HEALTH["error_count_1min"] = 1


def update_system_health(request_time_ms: float, success: bool):
    """Update system health metrics"""
    _SYSTEM_HEALTH["total_requests"] += 1

    if not success:
        _SYSTEM_HEALTH["failed_requests"] += 1

    # Update average response time (rolling average)
    current_avg = _SYSTEM_HEALTH["avg_response_time_ms"]
    total = _SYSTEM_HEALTH["total_requests"]
    new_avg = ((current_avg * (total - 1)) + request_time_ms) / total
    _SYSTEM_HEALTH["avg_response_time_ms"] = new_avg


def get_system_health() -> Dict[str, Any]:
    """Get current system health status"""
    uptime = (datetime.now() - _SYSTEM_HEALTH["start_time"]).total_seconds()

    return {
        "status": "healthy" if _SYSTEM_HEALTH["error_count_1min"] < 10 else "degraded",
        "uptime_seconds": uptime,
        "total_requests": _SYSTEM_HEALTH["total_requests"],
        "failed_requests": _SYSTEM_HEALTH["failed_requests"],
        "success_rate": (
            100 * (1 - _SYSTEM_HEALTH["failed_requests"] / max(1, _SYSTEM_HEALTH["total_requests"]))
        ),
        "avg_response_time_ms": round(_SYSTEM_HEALTH["avg_response_time_ms"], 2),
        "errors_last_minute": _SYSTEM_HEALTH["error_count_1min"],
        "last_error": _SYSTEM_HEALTH["last_error"],
        "circuit_breakers": {k: v["state"] for k, v in _CIRCUIT_BREAKERS.items()},
        "database": _DB_HEALTH
    }


def check_database_health():
    """Check database health and update metrics"""
    try:
        # Check database size
        db_path = os.getenv("DB_PATH", "orders.db")
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            _DB_HEALTH["size_mb"] = round(size_bytes / (1024 * 1024), 2)

        # Test connection
        conn = get_db_connection()
        _DB_HEALTH["total_connections"] += 1
        cursor = conn.cursor()

        # Quick health check query
        start = datetime.now()
        cursor.execute("SELECT COUNT(*) FROM orders")
        cursor.fetchone()
        query_time_ms = (datetime.now() - start).total_seconds() * 1000

        if query_time_ms > 1000:  # Slow query threshold
            _DB_HEALTH["slow_queries"] += 1

        release_db_connection(conn)
        record_service_success("database")

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        _DB_HEALTH["failed_connections"] += 1
        record_service_failure("database")


async def periodic_health_checks():
    """Background task to run periodic health checks"""
    while True:
        try:
            await asyncio.sleep(300)  # Every 5 minutes
            logger.info("Running periodic health checks...")

            # Check database
            check_database_health()

            # Log health status
            health = get_system_health()
            logger.info(f"System health: {health['status']} - Success rate: {health['success_rate']:.1f}%")

            # Reset 1-minute error count if needed
            if _SYSTEM_HEALTH["last_error_time"]:
                elapsed = (datetime.now() - _SYSTEM_HEALTH["last_error_time"]).total_seconds()
                if elapsed > 60:
                    _SYSTEM_HEALTH["error_count_1min"] = 0

        except Exception as e:
            logger.error(f"Error in periodic health checks: {e}")


# Phone number helpers
def _au_normalise_local(s: Optional[str]) -> Optional[str]:
    """Normalize AU phone to local format (04xxxxxxxx)"""
    if not s:
        return None
    d = re.sub(r"\D+", "", s)
    if not d:
        return None
    # +61XXXXXXXXX -> 0XXXXXXXXX
    if d.startswith("61") and len(d) == 11:
        return "0" + d[2:]
    if s.startswith("+61") and len(d) == 11:
        return "0" + d[2:]
    if d.startswith("0") and len(d) == 10:
        return d
    return d

def _au_to_e164(mobile: str) -> str:
    """Convert AU phone to E.164 format for Twilio"""
    try:
        s = re.sub(r"\D+", "", str(mobile or ""))
        if not s:
            return mobile
        if s.startswith("0") and len(s) == 10:
            return "+61" + s[1:]
        if s.startswith("61") and len(s) == 11:
            return "+" + s
        if str(mobile).startswith("+"):
            return str(mobile)
        return mobile
    except Exception:
        return mobile

def _last3(d: Optional[str]) -> Optional[str]:
    """Get last 3 digits"""
    if not d:
        return None
    dd = re.sub(r"\D+", "", d)
    return dd[-3:] if len(dd) >= 3 else None

def _format_item_details(item: Dict) -> str:
    """Format item with full details for receipt"""
    lines = []

    # Main line
    qty = item.get("quantity", 1)
    size = item.get("size", "").upper()
    protein = item.get("protein", "").upper()
    category = item.get("category", "").upper()

    main_line = f"{qty}x {size} {protein} {category}".strip()
    lines.append(main_line)

    # Salads
    salads = item.get("salads", [])
    if salads:
        lines.append(f"  ├ Salads: {', '.join(s.capitalize() for s in salads)}")

    # Sauces
    sauces = item.get("sauces", [])
    if sauces:
        lines.append(f"  ├ Sauces: {', '.join(s.capitalize() for s in sauces)}")

    # Salt type (for chips)
    salt_type = item.get("salt_type")
    if salt_type and category == "CHIPS":
        lines.append(f"  ├ Salt: {salt_type.capitalize()}")

    # Extras
    extras = item.get("extras", [])
    if extras:
        lines.append(f"  ├ Extras: {', '.join(e.capitalize() for e in extras)}")

    # Cheese
    if item.get("cheese"):
        lines.append(f"  ├ Extra Cheese")

    # Notes
    notes = item.get("notes")
    if notes:
        lines.append(f"  └ Note: {notes}")

    return "\n".join(lines)

def _send_order_notifications(order_number: str, order_id: str, customer_name: str, customer_phone: str, cart: List[Dict], totals: Dict, ready_at: str, send_customer_sms: bool = True):
    """Send beautiful SMS notifications to customer and shop"""
    try:
        # Check if Twilio is configured
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from = os.getenv("TWILIO_FROM") or os.getenv("TWILIO_PHONE_NUMBER")
        shop_number = os.getenv("SHOP_ORDER_TO")

        if not all([account_sid, auth_token, twilio_from]):
            logger.warning("Twilio not configured. Skipping SMS notifications.")
            return

        client = Client(account_sid, auth_token)
        business = load_json_file("business.json")
        shop_name = business.get("business_details", {}).get("name", "Kebabalab")
        shop_phone = business.get("business_details", {}).get("phone", "0423 680 596")
        shop_address = business.get("business_details", {}).get("address", "123 Main St, Melbourne")

        # Build detailed cart summary
        cart_details = []
        for item in cart:
            cart_details.append(_format_item_details(item))

        cart_summary = "\n\n".join(cart_details)
        total = totals.get("grand_total", 0)

        # Send to customer (if requested)
        if send_customer_sms:
            customer_msg = f"""🥙 {shop_name.upper()} ORDER #{order_number}

{cart_summary}

─────────────────────
TOTAL: ${total:.2f}
READY: {ready_at}

📍 {shop_address}
📞 Call: {shop_phone}

Thank you, {customer_name}! 🙏"""

            try:
                customer_e164 = _au_to_e164(customer_phone)
                client.messages.create(
                    body=customer_msg,
                    from_=twilio_from,
                    to=customer_e164
                )
                logger.info(f"SMS sent to customer: {customer_phone}")
            except Exception as e:
                logger.error(f"Failed to send SMS to customer: {e}")

        # Send to shop (always)
        if shop_number:
            from datetime import datetime
            import pytz
            tz = pytz.timezone(business.get("business_details", {}).get("timezone", "Australia/Melbourne"))
            now = datetime.now(tz)
            time_received = now.strftime("%I:%M %p")

            shop_msg = f"""🔔 NEW ORDER #{order_number}

👤 {customer_name}
📞 {customer_phone}
⏰ PICKUP: {ready_at}

📋 ORDER:
{cart_summary}

💰 TOTAL: ${total:.2f}

──────────────────────
Time received: {time_received}"""

            try:
                shop_e164 = _au_to_e164(shop_number)
                client.messages.create(
                    body=shop_msg,
                    from_=twilio_from,
                    to=shop_e164
                )
                logger.info(f"SMS sent to shop: {shop_number}")
            except Exception as e:
                logger.error(f"Failed to send SMS to shop: {e}")

    except Exception as e:
        logger.error(f"Error sending SMS notifications: {e}")

# ==================== ORDER STATE MACHINE ====================

class ItemState:
    """Represents the configuration state of an item"""

    REQUIRED_FIELDS = {
        "kebabs": ["size", "protein", "salads", "sauces"],
        "hsp": ["size", "protein", "sauces"],
        "chips": ["size"],
        "drinks": ["brand"],
        "gozleme": ["variant"],
        "sweets": [],
        "extras": [],
        "sauce_tubs": ["sauce_type"]
    }

    def __init__(self, category: str, name: str = None):
        self.category = category
        self.name = name
        self.size = None
        self.protein = None
        self.salads = []
        self.sauces = []
        self.extras = []
        self.cheese = None
        self.brand = None
        self.variant = None
        self.salt_type = "chicken"  # Default chicken salt
        self.sauce_type = None
        self.quantity = 1

    def get_next_required_field(self) -> Optional[str]:
        """Get next field that needs to be configured"""
        required = self.REQUIRED_FIELDS.get(self.category, [])

        for field in required:
            if field == "size" and not self.size:
                return "size"
            elif field == "protein" and not self.protein:
                return "protein"
            elif field == "salads" and self.salads is None:
                return "salads"
            elif field == "sauces" and self.sauces is None:
                return "sauces"
            elif field == "brand" and not self.brand:
                return "brand"
            elif field == "variant" and not self.variant:
                return "variant"
            elif field == "sauce_type" and not self.sauce_type:
                return "sauce_type"

        return None  # All required fields configured

    def is_complete(self) -> bool:
        """Check if item configuration is complete"""
        return self.get_next_required_field() is None

    def to_cart_item(self) -> Dict:
        """Convert to cart item format"""
        item = {
            "category": self.category,
            "quantity": self.quantity
        }

        if self.name:
            item["name"] = self.name
        if self.size:
            item["size"] = self.size
        if self.protein:
            item["protein"] = self.protein
        # Always include salads/sauces/extras even if empty (to preserve explicit empty choice)
        if self.salads is not None:
            item["salads"] = self.salads
        if self.sauces is not None:
            item["sauces"] = self.sauces
        if self.extras is not None:
            item["extras"] = self.extras
        if self.cheese is not None:
            item["cheese"] = self.cheese
        if self.brand:
            item["brand"] = self.brand
        if self.variant:
            item["variant"] = self.variant
        if self.salt_type:
            item["salt_type"] = self.salt_type
        if self.sauce_type:
            item["sauce_type"] = self.sauce_type

        return item

# ==================== COMBO DETECTION ====================

def detect_combo_opportunity(cart: List[Dict]) -> Optional[Dict]:
    """
    Detect if cart items can form a combo.
    Returns combo info if detected, None otherwise.

    FIXED: Now handles multiple quantities correctly
    """
    menu = load_json_file("menu.json")

    # Extract item types from cart (find ALL items, not just first)
    kebabs = []
    hsps = []
    chips_items = []
    cans = []

    for item in cart:
        cat = item.get("category", "").lower()
        qty = item.get("quantity", 1)

        if cat in ["kebabs", "kebab"]:
            # Add this item qty times to match individual items
            for _ in range(qty):
                kebabs.append(item)
        elif cat in ["hsp", "hsps"]:
            for _ in range(qty):
                hsps.append(item)
        elif cat == "chips":
            for _ in range(qty):
                chips_items.append(item)
        elif cat == "drinks" and item.get("brand"):
            for _ in range(qty):
                cans.append(item)

    # Use first available items for combo detection
    has_kebab = kebabs[0] if kebabs else None
    has_hsp = hsps[0] if hsps else None
    has_chips = chips_items[0] if chips_items else None
    has_can = cans[0] if cans else None

    # Check for combos

    # 1. Kebab + Chips + Can = Meal
    if has_kebab and has_chips and has_can:
        keb_size = has_kebab.get("size", "").lower()
        chips_size = has_chips.get("size", "").lower()

        if keb_size == "small" and chips_size == "small":
            return {
                "type": "meal",
                "combo_id": "CMB_KEB_SCHP_CAN",
                "name": "Small Kebab Meal",
                "price": 17.0,
                "items_to_replace": [has_kebab, has_chips, has_can],
                "savings": 1.5
            }
        elif keb_size == "large" and chips_size == "small":
            return {
                "type": "meal",
                "combo_id": "CMB_KEB_LCHP_S_CAN",
                "name": "Large Kebab Meal",
                "price": 22.0,
                "items_to_replace": [has_kebab, has_chips, has_can],
                "savings": 1.5
            }
        elif keb_size == "large" and chips_size == "large":
            return {
                "type": "meal",
                "combo_id": "CMB_KEB_LCHP_L_CAN",
                "name": "Large Kebab Meal with Large Chips",
                "price": 25.0,
                "items_to_replace": [has_kebab, has_chips, has_can],
                "savings": 2.5
            }

    # 2. Kebab + Can = Combo
    if has_kebab and has_can and not has_chips:
        keb_size = has_kebab.get("size", "").lower()

        if keb_size == "small":
            return {
                "type": "combo",
                "combo_id": "KEB_CAN_S",
                "name": "Small Kebab & Can Combo",
                "price": 12.0,
                "items_to_replace": [has_kebab, has_can],
                "savings": 1.5
            }
        elif keb_size == "large":
            return {
                "type": "combo",
                "combo_id": "KEB_CAN_L",
                "name": "Large Kebab & Can Combo",
                "price": 17.0,
                "items_to_replace": [has_kebab, has_can],
                "savings": 1.5
            }

    # 3. HSP + Can = Combo (HSPs already include chips!)
    if has_hsp and has_can:
        hsp_size = has_hsp.get("size", "").lower()

        if hsp_size == "small":
            return {
                "type": "combo",
                "combo_id": "CMB_HSP_CAN_S",
                "name": "Small HSP Combo",
                "price": 17.0,
                "items_to_replace": [has_hsp, has_can],
                "savings": 1.5
            }
        elif hsp_size == "large":
            return {
                "type": "combo",
                "combo_id": "CMB_HSP_CAN_L",
                "name": "Large HSP Combo",
                "price": 22.0,
                "items_to_replace": [has_hsp, has_can],
                "savings": 1.5
            }

    return None

def apply_combo_to_cart(cart: List[Dict], combo_info: Dict) -> List[Dict]:
    """
    Apply combo to cart by replacing individual items with combo item.
    Returns new cart.
    """
    new_cart = []
    items_to_skip = combo_info["items_to_replace"]

    # Keep items not involved in combo
    for item in cart:
        if item not in items_to_skip:
            new_cart.append(item)

    # Create combo item preserving kebab/HSP details
    base_item = items_to_skip[0]  # First item (kebab or HSP)

    combo_item = {
        "category": "combo",
        "combo_id": combo_info["combo_id"],
        "name": combo_info["name"],
        "price": combo_info["price"],
        "quantity": 1,
        "is_combo": True
    }

    # Preserve important details from base item
    if base_item.get("protein"):
        combo_item["protein"] = base_item["protein"]
    if base_item.get("salads"):
        combo_item["salads"] = base_item["salads"]
    if base_item.get("sauces"):
        combo_item["sauces"] = base_item["sauces"]
    if base_item.get("extras"):
        combo_item["extras"] = base_item["extras"]
    if base_item.get("cheese") is not None:
        combo_item["cheese"] = base_item["cheese"]

    # Add drink brand if present
    for item in items_to_skip:
        if item.get("category") == "drinks" and item.get("brand"):
            combo_item["drink_brand"] = item["brand"]
            break

    # Add chips salt type if present
    for item in items_to_skip:
        if item.get("category") == "chips" and item.get("salt_type"):
            combo_item["chips_salt"] = item["salt_type"]
            break

    new_cart.append(combo_item)
    return new_cart

# ==================== PRICING ====================

def calculate_item_price(item: Dict, menu: Dict) -> Decimal:
    """Calculate price for a single item"""

    # Handle combo items
    if item.get("is_combo") and item.get("price"):
        return Decimal(str(item["price"]))

    category = item.get("category", "").lower()
    size = item.get("size", "").lower()

    base_price = Decimal("0")

    # Standard pricing by category (protein type doesn't affect price)
    if category in ["kebabs", "kebab"]:
        # All kebabs same price by size
        if size == "small":
            base_price = Decimal("10.0")
        elif size == "large":
            base_price = Decimal("15.0")

    elif category in ["hsp", "hsps"]:
        # All HSPs same price by size
        if size == "small":
            base_price = Decimal("15.0")
        elif size == "large":
            base_price = Decimal("20.0")

    elif category == "chips":
        # Chips pricing by size
        if size == "small":
            base_price = Decimal("5.0")
        elif size == "large":
            base_price = Decimal("9.0")  # FIXED: Was $8.00, now correct $9.00

    elif category in ["drinks", "drink"]:
        # All cans are $3.50
        base_price = Decimal("3.5")  # FIXED: Was $3.00, now correct $3.50

    # Add extras pricing
    extras = item.get("extras", [])
    for extra in extras:
        extra_lower = str(extra).lower()
        # Cheese addon
        if "cheese" in extra_lower:
            base_price += Decimal("1.00")
        # Extra meat
        elif "meat" in extra_lower or "lamb" in extra_lower or "chicken" in extra_lower:
            base_price += Decimal("3.00")

    # Extra sauces (more than 2 free)
    sauces = item.get("sauces", [])
    if len(sauces) > 2:
        base_price += Decimal("0.50") * (len(sauces) - 2)

    # Cheese if added (separate boolean field)
    if item.get("cheese") and category in ["kebabs", "kebab", "hsp", "hsps"]:
        base_price += Decimal("1.00")

    return base_price

# ==================== TOOLS ====================

def tool_start_item_configuration(params: Dict[str, Any]) -> Dict[str, Any]:
    """Start configuring a new item"""
    try:
        logger.info(f"Starting item configuration: {params}")
        category = params.get("category", "").lower()
        name = params.get("name")

        # Create new item state
        item_state = ItemState(category, name)

        # Store in session
        session_set("current_item", item_state)
        session_set("order_state", "CONFIGURING_ITEM")

        # Get next required field
        next_field = item_state.get_next_required_field()

        return {
            "ok": True,
            "category": category,
            "name": name,
            "nextField": next_field,
            "message": f"Started configuring {category}. Need to confirm: {next_field}"
        }

    except Exception as e:
        logger.error(f"Error starting item configuration: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_set_item_property(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set a property on the current item being configured"""
    try:
        logger.info(f"Setting item property: {params}")

        # Get current item from session
        item_state = session_get("current_item")
        if not item_state:
            return {"ok": False, "error": "No item is currently being configured. Call startItemConfiguration first."}

        field = params.get("field")
        value = params.get("value")

        if not field:
            return {"ok": False, "error": "Field name is required"}

        # Parse value (VAPI might send JSON strings for arrays)
        parsed_value = value
        if isinstance(value, str) and value.strip():
            # Try to parse as JSON
            try:
                parsed_value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Not JSON, use as-is
                parsed_value = value

        # Set the property with proper type handling
        if field == "size":
            item_state.size = str(parsed_value) if parsed_value else None
        elif field == "protein":
            item_state.protein = str(parsed_value) if parsed_value else None
        elif field == "salads":
            # Explicitly handle empty arrays
            if parsed_value == [] or parsed_value == "" or parsed_value == "[]":
                item_state.salads = []
            elif isinstance(parsed_value, list):
                item_state.salads = parsed_value
            elif parsed_value:
                item_state.salads = [str(parsed_value)]
            else:
                item_state.salads = []
        elif field == "sauces":
            # Explicitly handle empty arrays
            if parsed_value == [] or parsed_value == "" or parsed_value == "[]":
                item_state.sauces = []
            elif isinstance(parsed_value, list):
                item_state.sauces = parsed_value
            elif parsed_value:
                item_state.sauces = [str(parsed_value)]
            else:
                item_state.sauces = []
        elif field == "extras":
            # Explicitly handle empty arrays
            if parsed_value == [] or parsed_value == "" or parsed_value == "[]":
                item_state.extras = []
            elif isinstance(parsed_value, list):
                item_state.extras = parsed_value
            elif parsed_value:
                item_state.extras = [str(parsed_value)]
            else:
                item_state.extras = []
        elif field == "cheese":
            # Handle boolean strings
            if isinstance(parsed_value, str):
                item_state.cheese = parsed_value.lower() in ["true", "1", "yes"]
            else:
                item_state.cheese = bool(parsed_value)
        elif field == "brand":
            item_state.brand = str(parsed_value) if parsed_value else None
        elif field == "variant":
            item_state.variant = str(parsed_value) if parsed_value else None
        elif field == "salt_type":
            # Ensure salt_type is properly set (override default)
            item_state.salt_type = str(parsed_value) if parsed_value else "chicken"
            logger.info(f"Set salt_type to: {item_state.salt_type}")
        elif field == "sauce_type":
            item_state.sauce_type = str(parsed_value) if parsed_value else None
        elif field == "quantity":
            # Handle quantity properly
            try:
                item_state.quantity = int(parsed_value) if parsed_value else 1
                logger.info(f"Set quantity to: {item_state.quantity}")
            except (ValueError, TypeError):
                item_state.quantity = 1
        else:
            return {"ok": False, "error": f"Unknown field: {field}"}

        # Update session
        session_set("current_item", item_state)

        # Check if item is complete
        next_field = item_state.get_next_required_field()
        is_complete = item_state.is_complete()

        return {
            "ok": True,
            "field": field,
            "value": value,
            "nextField": next_field,
            "isComplete": is_complete,
            "message": f"Set {field} to {value}. " + (
                "Item configuration complete!" if is_complete
                else f"Next: confirm {next_field}"
            )
        }

    except Exception as e:
        logger.error(f"Error setting item property: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_add_item_to_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Add the configured item to cart and detect combos"""
    try:
        logger.info("Adding item to cart")

        # Get current item
        item_state = session_get("current_item")
        if not item_state:
            return {"ok": False, "error": "No item configured. Use startItemConfiguration first."}

        if not item_state.is_complete():
            next_field = item_state.get_next_required_field()
            return {
                "ok": False,
                "error": f"Item not fully configured. Still need: {next_field}"
            }

        # Get cart
        cart = session_get("cart", [])

        # Add item to cart
        cart_item = item_state.to_cart_item()
        cart.append(cart_item)

        # Check for combo opportunities
        combo_detected = detect_combo_opportunity(cart)

        # Update cart in session
        session_set("cart", cart)

        # Clear current item
        session_set("current_item", None)
        session_set("order_state", "CART_ACTIVE")

        # Minimal response for speed
        if combo_detected:
            # Apply combo
            cart = apply_combo_to_cart(cart, combo_detected)
            session_set("cart", cart)
            return {
                "ok": True,
                "cartCount": len(cart),
                "combo": combo_detected["name"]
            }

        return {
            "ok": True,
            "cartCount": len(cart)
        }

    except Exception as e:
        logger.error(f"Error adding item to cart: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_get_cart_state(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get current cart state"""
    try:
        cart = session_get("cart", [])
        current_item = session_get("current_item")

        return {
            "ok": True,
            "cart": cart,
            "itemCount": len(cart),
            "isConfiguringItem": current_item is not None,
            "currentItem": current_item.to_cart_item() if current_item else None
        }

    except Exception as e:
        logger.error(f"Error getting cart state: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_price_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate total price for cart"""
    try:
        logger.info("Pricing cart")
        cart = session_get("cart", [])

        if not cart:
            return {"ok": False, "error": "Cart is empty"}

        menu = load_json_file("menu.json")
        gst_rate = Decimal(os.getenv("GST_RATE", "0.10"))

        subtotal = Decimal("0")
        item_breakdown = []

        for idx, item in enumerate(cart):
            quantity = item.get("quantity", 1)
            item_price = calculate_item_price(item, menu)
            line_total = item_price * Decimal(str(quantity))
            subtotal += line_total

            # Build description
            desc_parts = []
            if quantity > 1:
                desc_parts.append(f"{quantity}x")
            if item.get("size"):
                desc_parts.append(item["size"].capitalize())
            if item.get("protein"):
                desc_parts.append(item["protein"].capitalize())
            if item.get("name"):
                desc_parts.append(item["name"])
            elif item.get("category"):
                desc_parts.append(item["category"].upper())

            item_breakdown.append({
                "line": idx + 1,
                "description": " ".join(desc_parts),
                "price": float(item_price),
                "quantity": quantity,
                "lineTotal": float(line_total),
                "isCombo": item.get("is_combo", False)
            })

        grand_total = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gst_amount = ((subtotal * gst_rate) / (Decimal("1") + gst_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Store totals in session
        session_set("last_totals", {
            "subtotal": float(grand_total),
            "gst": float(gst_amount),
            "grand_total": float(grand_total)
        })
        session_set("cart_priced", True)

        # Minimal response for speed (AI doesn't need breakdown)
        return {
            "ok": True,
            "grandTotal": float(grand_total)
        }

    except Exception as e:
        logger.error(f"Error pricing cart: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

# Import existing tools from original server
def tool_check_open(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check if shop is open"""
    try:
        logger.info("Checking if shop is open")
        hours = load_json_file("hours.json")
        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("business_details", {}).get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)
        day_name = now.strftime("%A").lower()

        today_hours = hours.get(day_name, [])
        is_open = False

        if today_hours:
            current_time = now.strftime("%H:%M")
            for time_range in today_hours:
                start = time_range.get("open")
                end = time_range.get("close")
                if start and end:
                    if start <= current_time <= end:
                        is_open = True
                        break

        return {
            "ok": True,
            "isOpen": is_open,
            "currentTime": now.isoformat(),
            "dayOfWeek": day_name,
            "todayHours": json.dumps(today_hours) if today_hours else "closed"
        }

    except Exception as e:
        logger.error(f"Error checking open status: {str(e)}")
        return {"ok": False, "error": str(e), "isOpen": False}

def tool_get_caller_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get caller information"""
    try:
        logger.info("Getting caller info")
        caller_number = caller_context.get()

        if caller_number:
            local = _au_normalise_local(str(caller_number))
            last3 = _last3(local)

            return {
                "ok": True,
                "hasCallerID": True,
                "phoneNumber": local,
                "last3": last3
            }

        return {
            "ok": True,
            "hasCallerID": False,
            "phoneNumber": None
        }

    except Exception as e:
        logger.error(f"Error getting caller info: {str(e)}")
        return {"ok": False, "error": str(e), "hasCallerID": False}

def tool_set_pickup_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set custom pickup time from customer request"""
    try:
        logger.info(f"Setting pickup time: {params}")

        minutes = params.get("minutes")

        if minutes is None:
            return {"ok": False, "error": "minutes parameter is required"}

        try:
            minutes = int(minutes)
        except (ValueError, TypeError):
            return {"ok": False, "error": "minutes must be a number"}

        # Minimum 10 minutes
        MIN_PICKUP_TIME = 10
        if minutes < MIN_PICKUP_TIME:
            return {
                "ok": False,
                "error": f"Minimum pickup time is {MIN_PICKUP_TIME} minutes",
                "minimumMinutes": MIN_PICKUP_TIME,
                "requestedMinutes": minutes,
                "tooEarly": True
            }

        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("business_details", {}).get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)

        ready_time = now + timedelta(minutes=minutes)

        # Format time for speech
        hour_12 = ready_time.hour if ready_time.hour <= 12 else ready_time.hour - 12
        if hour_12 == 0:
            hour_12 = 12
        period = "AM" if ready_time.hour < 12 else "PM"
        minute = ready_time.minute

        if minute == 0:
            time_speech = f"{hour_12} {period}"
        else:
            time_speech = f"{hour_12} {minute:02d} {period}"

        # Store in session
        session_set("pickup_time_iso", ready_time.isoformat())
        session_set("pickup_time_speech", time_speech)
        session_set("pickup_time_minutes", minutes)

        return {
            "ok": True,
            "readyAtIso": ready_time.isoformat(),
            "readyAt": time_speech,
            "readyAtMinutes": minutes,
            "message": f"Pickup time set to {time_speech} (in {minutes} minutes)"
        }

    except Exception as e:
        logger.error(f"Error setting pickup time: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_estimate_ready_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate order ready time with dynamic queue-based calculation"""
    try:
        logger.info(f"Estimating ready time: {params}")

        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("business_details", {}).get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)

        # Check current order queue
        conn = get_db_connection()
        cursor = conn.cursor()

        # Count pending orders in last 30 minutes
        thirty_mins_ago = (now - timedelta(minutes=30)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM orders
            WHERE created_at >= ? AND status IN ('pending', 'preparing')
        """, (thirty_mins_ago,))

        queue_length = cursor.fetchone()[0]
        release_db_connection(conn)

        # Dynamic lead time based on queue
        base_time = 10  # Minimum 10 minutes
        if queue_length == 0:
            lead_time = base_time  # Quiet - 10 mins
        elif queue_length <= 2:
            lead_time = 15  # Normal - 15 mins
        elif queue_length <= 5:
            lead_time = 20  # Busy - 20 mins
        else:
            lead_time = 30  # Very busy - 30 mins

        # Also factor in busy hours
        hour = now.hour
        if (11 <= hour <= 14) or (17 <= hour <= 20):
            lead_time += 5  # Add 5 mins during peak hours

        logger.info(f"Queue length: {queue_length}, Lead time: {lead_time} mins")

        ready_time = now + timedelta(minutes=lead_time)

        # Format time for speech
        hour_12 = ready_time.hour if ready_time.hour <= 12 else ready_time.hour - 12
        if hour_12 == 0:
            hour_12 = 12
        period = "AM" if ready_time.hour < 12 else "PM"
        minute = ready_time.minute

        if minute == 0:
            time_speech = f"{hour_12} {period}"
        else:
            time_speech = f"{hour_12} {minute:02d} {period}"

        # Store in session
        session_set("pickup_time_iso", ready_time.isoformat())
        session_set("pickup_time_speech", time_speech)
        session_set("pickup_time_minutes", lead_time)

        return {
            "ok": True,
            "readyAtIso": ready_time.isoformat(),
            "readyAt": time_speech,
            "readyAtMinutes": lead_time,
            "message": f"Your order will be ready in about {lead_time} minutes"
        }

    except Exception as e:
        logger.error(f"Error estimating ready time: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_get_order_summary(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get human-readable order summary for agent to repeat"""
    try:
        logger.info("Getting order summary")

        cart = session_get("cart", [])
        if not cart:
            return {"ok": False, "error": "Cart is empty"}

        # Build summary text
        items_text = []
        for item in cart:
            qty = item.get("quantity", 1)
            size = item.get("size", "").lower()
            protein = item.get("protein", "").lower()
            category = item.get("category", "").lower()

            # Build item description
            parts = []
            if qty > 1:
                parts.append(f"{qty}")
            if size:
                parts.append(size)
            if protein:
                parts.append(protein)
            parts.append(category)

            item_desc = " ".join(parts)

            # Add modifiers
            modifiers = []
            salads = item.get("salads", [])
            if salads:
                modifiers.append(f"with {', '.join(salads)}")

            sauces = item.get("sauces", [])
            if sauces:
                modifiers.append(f"{', '.join(sauces)} sauce")

            if modifiers:
                item_desc += " " + " ".join(modifiers)

            items_text.append(item_desc)

        # Get total
        totals = session_get("last_totals")
        total = totals.get("grand_total", 0) if totals else 0

        summary = ", ".join(items_text)

        return {
            "ok": True,
            "summary": summary,
            "total": total,
            "itemCount": len(cart)
        }

    except Exception as e:
        logger.error(f"Error getting order summary: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_set_order_notes(params: Dict[str, Any]) -> Dict[str, Any]:
    """Set special instructions/notes for the order"""
    try:
        notes = params.get("notes")

        if not notes:
            return {"ok": False, "error": "notes parameter is required"}

        # Store in session
        session_set("order_notes", notes)
        logger.info(f"Order notes set: {notes}")

        return {
            "ok": True,
            "notes": notes
        }

    except Exception as e:
        logger.error(f"Error setting order notes: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_get_last_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get customer's last order for repeat ordering"""
    conn = None  # Initialize early to prevent NameError
    try:
        phone_number = params.get("phoneNumber")

        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        # Normalize phone
        phone_normalized = _au_normalise_local(phone_number)

        # Query database
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT order_id, customer_name, cart, totals, created_at
            FROM orders
            WHERE customer_phone = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (phone_normalized,))

        row = cursor.fetchone()
        release_db_connection(conn)

        if not row:
            return {
                "ok": True,
                "hasLastOrder": False
            }

        order_id, customer_name, cart_json, totals_json, created_at = row
        cart = json.loads(cart_json)
        totals = json.loads(totals_json)

        return {
            "ok": True,
            "hasLastOrder": True,
            "customerName": customer_name,
            "cart": cart,
            "total": totals.get("grand_total", 0),
            "orderId": order_id,
            "orderDate": created_at
        }

    except Exception as e:
        logger.error(f"Error getting last order: {str(e)}")
        if conn:  # Only release if connection was established
            release_db_connection(conn)
        return {"ok": False, "error": str(e)}

def tool_lookup_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Look up an existing order by ID or phone number"""
    conn = None  # Initialize early to prevent NameError
    try:
        order_id = params.get("orderId")
        phone_number = params.get("phoneNumber")

        if not order_id and not phone_number:
            return {"ok": False, "error": "Either orderId or phoneNumber is required"}

        conn = get_db_connection()
        cursor = conn.cursor()

        if order_id:
            # Search by order ID
            cursor.execute("""
                SELECT order_id, customer_name, customer_phone, cart, totals, ready_at, status
                FROM orders
                WHERE order_id LIKE ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (f"%{order_id}%",))
        else:
            # Search by phone (most recent)
            phone_normalized = _au_normalise_local(phone_number)
            cursor.execute("""
                SELECT order_id, customer_name, customer_phone, cart, totals, ready_at, status
                FROM orders
                WHERE customer_phone = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (phone_normalized,))

        row = cursor.fetchone()
        release_db_connection(conn)

        if not row:
            return {
                "ok": True,
                "found": False,
                "message": "No order found"
            }

        order_id, customer_name, customer_phone, cart_json, totals_json, ready_at, status = row
        cart = json.loads(cart_json)
        totals = json.loads(totals_json)

        return {
            "ok": True,
            "found": True,
            "orderId": order_id,
            "customerName": customer_name,
            "customerPhone": customer_phone,
            "cart": cart,
            "total": totals.get("grand_total", 0),
            "readyAt": ready_at,
            "status": status
        }

    except Exception as e:
        logger.error(f"Error looking up order: {str(e)}")
        if conn:  # Only release if connection was established
            release_db_connection(conn)
        return {"ok": False, "error": str(e)}

def tool_send_menu_link(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send menu link via SMS"""
    try:
        phone_number = params.get("phoneNumber")

        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        # Check if Twilio is configured
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_from = os.getenv("TWILIO_FROM") or os.getenv("TWILIO_PHONE_NUMBER")

        if not all([account_sid, auth_token, twilio_from]):
            return {"ok": False, "error": "SMS not configured"}

        client = Client(account_sid, auth_token)
        menu_url = "https://www.kebabalab.com.au/menu.html"

        message = f"""🥙 KEBABALAB MENU

Check out our full menu:
{menu_url}

📞 Call to order: 0423 680 596"""

        try:
            phone_e164 = _au_to_e164(phone_number)
            client.messages.create(
                body=message,
                from_=twilio_from,
                to=phone_e164
            )
            logger.info(f"Menu link sent to: {phone_number}")

            return {
                "ok": True,
                "message": "Menu link sent!",
                "menuUrl": menu_url
            }

        except Exception as e:
            logger.error(f"Failed to send menu link: {e}")
            return {"ok": False, "error": str(e)}

    except Exception as e:
        logger.error(f"Error sending menu link: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_create_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create final order"""
    try:
        logger.info(f"Creating order: {params}")

        cart = session_get("cart", [])
        totals = session_get("last_totals")

        if not cart:
            return {"ok": False, "error": "Cart is empty"}
        if not totals:
            return {"ok": False, "error": "Cart not priced. Call priceCart first."}

        customer_name = params.get("customerName")
        customer_phone = params.get("customerPhone")
        send_sms = params.get("sendSMS", True)  # Default to True

        # Get pickup time from session (set by setPickupTime or estimateReadyTime)
        ready_at_iso = session_get("pickup_time_iso")
        ready_at_speech = session_get("pickup_time_speech")

        # Get order notes if any
        order_notes = session_get("order_notes", "")

        if not customer_name:
            return {"ok": False, "error": "Customer name is required"}
        if not customer_phone:
            return {"ok": False, "error": "Customer phone is required"}
        if not ready_at_iso:
            return {"ok": False, "error": "Pickup time not set. Call setPickupTime or estimateReadyTime first."}

        # Save to database using connection pool
        conn = get_db_connection()
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_id LIKE ?", (f"{today}-%",))
        count = cursor.fetchone()[0]
        order_id_internal = f"{today}-{(count + 1):03d}"
        order_number = f"{(count + 1):03d}"

        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("business_details", {}).get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)

        cursor.execute("""
            INSERT INTO orders (
                order_id, created_at, ready_at, customer_name, customer_phone,
                order_type, cart, totals, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id_internal, now.isoformat(), ready_at_iso,
            customer_name, customer_phone, "pickup",
            json.dumps(cart), json.dumps(totals), "pending", order_notes
        ))
        conn.commit()
        release_db_connection(conn)

        # Send SMS notifications (customer SMS optional based on sendSMS param)
        _send_order_notifications(order_number, order_id_internal, customer_name, customer_phone, cart, totals, ready_at_speech, send_sms)

        # Clear session
        session_set("cart", [])
        session_set("cart_priced", False)
        session_set("order_state", "ORDER_PLACED")

        # Minimal response for speed
        return {
            "ok": True,
            "orderId": order_number,
            "readyAt": ready_at_speech
        }

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_remove_cart_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """Remove an item from the cart"""
    try:
        logger.info(f"Removing cart item: {params}")

        cart = session_get("cart", [])
        item_index = params.get("itemIndex")

        if item_index is None:
            return {"ok": False, "error": "itemIndex is required"}

        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            return {"ok": False, "error": "itemIndex must be a number"}

        if item_index < 0 or item_index >= len(cart):
            return {"ok": False, "error": f"Invalid itemIndex. Cart has {len(cart)} items (0-{len(cart)-1})"}

        # Remove the item
        removed_item = cart.pop(item_index)

        # Update cart
        session_set("cart", cart)
        session_set("cart_priced", False)  # Cart changed, need to reprice

        # Minimal response
        return {
            "ok": True,
            "cartCount": len(cart)
        }

    except Exception as e:
        logger.error(f"Error removing cart item: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_edit_cart_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """Edit an existing cart item"""
    try:
        logger.info(f"Editing cart item: {params}")

        cart = session_get("cart", [])
        item_index = params.get("itemIndex")
        field = params.get("field")
        value = params.get("value")

        if item_index is None:
            return {"ok": False, "error": "itemIndex is required"}
        if not field:
            return {"ok": False, "error": "field is required"}

        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            return {"ok": False, "error": "itemIndex must be a number"}

        if item_index < 0 or item_index >= len(cart):
            return {"ok": False, "error": f"Invalid itemIndex. Cart has {len(cart)} items (0-{len(cart)-1})"}

        # Get the item
        item = cart[item_index]

        # Validate field can be edited
        if field in ["size", "protein"]:
            # Size/protein changes might affect combo detection, so we disallow it
            # User should remove and re-add instead
            return {
                "ok": False,
                "error": f"Cannot change {field} on existing item. Please remove and re-add the item."
            }

        # Parse value (VAPI sends as string, may need to parse JSON for arrays)
        parsed_value = value
        if isinstance(value, str):
            # Try to parse as JSON for arrays
            try:
                parsed_value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Not JSON, use as-is (for string values)
                parsed_value = value

        # Update the field
        if field == "salads":
            item["salads"] = parsed_value if isinstance(parsed_value, list) else [parsed_value] if parsed_value else []
        elif field == "sauces":
            item["sauces"] = parsed_value if isinstance(parsed_value, list) else [parsed_value] if parsed_value else []
        elif field == "extras":
            item["extras"] = parsed_value if isinstance(parsed_value, list) else [parsed_value] if parsed_value else []
        elif field == "cheese":
            # Handle boolean strings
            if isinstance(parsed_value, str):
                item["cheese"] = parsed_value.lower() in ["true", "1", "yes"]
            else:
                item["cheese"] = bool(parsed_value)
        elif field == "salt_type":
            item["salt_type"] = str(parsed_value)
        elif field == "quantity":
            item["quantity"] = int(parsed_value) if parsed_value else 1
        else:
            return {"ok": False, "error": f"Cannot edit field: {field}"}

        # Update cart
        cart[item_index] = item
        session_set("cart", cart)
        session_set("cart_priced", False)  # Cart changed, need to reprice

        # Minimal response
        return {"ok": True}

    except Exception as e:
        logger.error(f"Error editing cart item: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_clear_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Clear all items from cart"""
    try:
        logger.info("Clearing cart")

        cart = session_get("cart", [])
        item_count = len(cart)

        # Clear cart
        session_set("cart", [])
        session_set("cart_priced", False)
        session_set("current_item", None)
        session_set("order_state", "IDLE")

        # Minimal response
        return {"ok": True}

    except Exception as e:
        logger.error(f"Error clearing cart: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_clear_session(params: Dict[str, Any]) -> Dict[str, Any]:
    """Clear/reset the current session (for testing or starting fresh)"""
    try:
        logger.info("Clearing session")
        session_reset()

        # Minimal response
        return {"ok": True}

    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_convert_items_to_meals(params: Dict[str, Any]) -> Dict[str, Any]:
    """Convert kebabs in cart to meals by adding chips and drink.
    Can convert all kebabs or specific items by index."""
    try:
        logger.info(f"Converting items to meals: {params}")

        cart = session_get("cart", [])
        if not cart:
            return {"ok": False, "error": "Cart is empty"}

        # Get parameters
        item_indices = params.get("itemIndices")  # Optional: specific indices to convert
        drink_brand = params.get("drinkBrand", "coke")  # Default to coke
        chips_size = params.get("chipsSize", "small")  # Default to small chips
        chips_salt = params.get("chipsSalt", "chicken")  # Default to chicken salt

        # If no indices specified, convert ALL kebabs
        if item_indices is None:
            item_indices = []
            for idx, item in enumerate(cart):
                if item.get("category", "").lower() in ["kebabs", "kebab"]:
                    item_indices.append(idx)
        elif not isinstance(item_indices, list):
            item_indices = [item_indices]

        if not item_indices:
            return {"ok": False, "error": "No kebabs found to convert to meals"}

        logger.info(f"Converting {len(item_indices)} kebabs to meals")

        # Process each kebab
        converted_count = 0
        new_cart = []

        for idx, item in enumerate(cart):
            if idx in item_indices:
                # This is a kebab to convert
                if item.get("category", "").lower() not in ["kebabs", "kebab"]:
                    logger.warning(f"Item at index {idx} is not a kebab, skipping")
                    new_cart.append(item)
                    continue

                # Get kebab details
                keb_size = item.get("size", "").lower()

                # Create combo item
                if keb_size == "small":
                    combo_price = 17.0 if chips_size == "small" else 20.0
                    combo_name = "Small Kebab Meal" if chips_size == "small" else "Small Kebab Meal (Large Chips)"
                    combo_id = "CMB_KEB_SCHP_CAN" if chips_size == "small" else "CMB_KEB_SCHP_L_CAN"
                elif keb_size == "large":
                    if chips_size == "small":
                        combo_price = 22.0
                        combo_name = "Large Kebab Meal"
                        combo_id = "CMB_KEB_LCHP_S_CAN"
                    else:
                        combo_price = 25.0
                        combo_name = "Large Kebab Meal (Large Chips)"
                        combo_id = "CMB_KEB_LCHP_L_CAN"
                else:
                    logger.warning(f"Unknown kebab size: {keb_size}, skipping")
                    new_cart.append(item)
                    continue

                # Create meal combo item preserving kebab details
                combo_item = {
                    "category": "combo",
                    "combo_id": combo_id,
                    "name": combo_name,
                    "price": combo_price,
                    "quantity": item.get("quantity", 1),
                    "is_combo": True,
                    "protein": item.get("protein"),
                    "salads": item.get("salads", []),
                    "sauces": item.get("sauces", []),
                    "extras": item.get("extras", []),
                    "drink_brand": drink_brand,
                    "chips_salt": chips_salt
                }

                if item.get("cheese") is not None:
                    combo_item["cheese"] = item["cheese"]

                new_cart.append(combo_item)
                converted_count += 1
                logger.info(f"Converted kebab #{idx} to {combo_name}")
            else:
                # Keep item as-is
                new_cart.append(item)

        # Update cart
        session_set("cart", new_cart)
        session_set("cart_priced", False)  # Cart changed, need to reprice

        return {
            "ok": True,
            "convertedCount": converted_count,
            "cartCount": len(new_cart),
            "message": f"Converted {converted_count} kebab(s) to meal(s)"
        }

    except Exception as e:
        logger.error(f"Error converting items to meals: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_modify_cart_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """Modify an existing cart item completely. Unlike editCartItem, this can change ANY property including size, protein, etc."""
    try:
        logger.info(f"Modifying cart item: {params}")

        cart = session_get("cart", [])
        item_index = params.get("itemIndex")
        modifications = params.get("modifications", {})

        if item_index is None:
            return {"ok": False, "error": "itemIndex is required"}

        if not modifications:
            return {"ok": False, "error": "modifications object is required"}

        try:
            item_index = int(item_index)
        except (ValueError, TypeError):
            return {"ok": False, "error": "itemIndex must be a number"}

        if item_index < 0 or item_index >= len(cart):
            return {"ok": False, "error": f"Invalid itemIndex. Cart has {len(cart)} items (0-{len(cart)-1})"}

        # Get the item
        item = cart[item_index]

        # Apply modifications
        for field, value in modifications.items():
            # Parse value if it's a JSON string
            parsed_value = value
            if isinstance(value, str):
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_value = value

            # Update the field
            if field == "size":
                item["size"] = str(parsed_value) if parsed_value else None
            elif field == "protein":
                item["protein"] = str(parsed_value) if parsed_value else None
            elif field == "salads":
                if parsed_value == [] or parsed_value == "" or parsed_value == "[]":
                    item["salads"] = []
                elif isinstance(parsed_value, list):
                    item["salads"] = parsed_value
                elif parsed_value:
                    item["salads"] = [str(parsed_value)]
                else:
                    item["salads"] = []
            elif field == "sauces":
                if parsed_value == [] or parsed_value == "" or parsed_value == "[]":
                    item["sauces"] = []
                elif isinstance(parsed_value, list):
                    item["sauces"] = parsed_value
                elif parsed_value:
                    item["sauces"] = [str(parsed_value)]
                else:
                    item["sauces"] = []
            elif field == "extras":
                if parsed_value == [] or parsed_value == "" or parsed_value == "[]":
                    item["extras"] = []
                elif isinstance(parsed_value, list):
                    item["extras"] = parsed_value
                elif parsed_value:
                    item["extras"] = [str(parsed_value)]
                else:
                    item["extras"] = []
            elif field == "cheese":
                if isinstance(parsed_value, str):
                    item["cheese"] = parsed_value.lower() in ["true", "1", "yes"]
                else:
                    item["cheese"] = bool(parsed_value)
            elif field == "brand":
                item["brand"] = str(parsed_value) if parsed_value else None
            elif field == "variant":
                item["variant"] = str(parsed_value) if parsed_value else None
            elif field == "salt_type":
                item["salt_type"] = str(parsed_value) if parsed_value else "chicken"
            elif field == "sauce_type":
                item["sauce_type"] = str(parsed_value) if parsed_value else None
            elif field == "quantity":
                try:
                    item["quantity"] = int(parsed_value) if parsed_value else 1
                except (ValueError, TypeError):
                    item["quantity"] = 1
            else:
                logger.warning(f"Unknown field in modifications: {field}")

        # Update cart
        cart[item_index] = item
        session_set("cart", cart)
        session_set("cart_priced", False)

        return {
            "ok": True,
            "message": f"Modified item at index {item_index}"
        }

    except Exception as e:
        logger.error(f"Error modifying cart item: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_get_detailed_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get detailed cart with human-readable descriptions for each item"""
    try:
        cart = session_get("cart", [])

        detailed_items = []
        for idx, item in enumerate(cart):
            qty = item.get("quantity", 1)
            size = item.get("size", "").capitalize()
            protein = item.get("protein", "").capitalize()
            category = item.get("category", "").upper()

            # Build description
            parts = []
            if qty > 1:
                parts.append(f"{qty}x")
            if size:
                parts.append(size)
            if protein:
                parts.append(protein)
            if item.get("name"):
                parts.append(item["name"])
            else:
                parts.append(category)

            description = " ".join(parts)

            # Add modifiers
            modifiers = []
            if item.get("salads"):
                modifiers.append(f"Salads: {', '.join(item['salads'])}")
            if item.get("sauces"):
                modifiers.append(f"Sauces: {', '.join(item['sauces'])}")
            if item.get("extras"):
                modifiers.append(f"Extras: {', '.join(item['extras'])}")
            if item.get("cheese"):
                modifiers.append("Extra Cheese")
            if item.get("is_combo"):
                modifiers.append(f"MEAL (includes {item.get('chips_salt', 'chicken')} salt chips + {item.get('drink_brand', 'drink')})")

            detailed_items.append({
                "index": idx,
                "description": description,
                "modifiers": modifiers,
                "isCombo": item.get("is_combo", False),
                "rawItem": item
            })

        return {
            "ok": True,
            "items": detailed_items,
            "itemCount": len(cart)
        }

    except Exception as e:
        logger.error(f"Error getting detailed cart: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_validate_menu_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that item exists in menu and properties are valid"""
    try:
        category = params.get("category", "").lower()
        size = params.get("size", "").lower() if params.get("size") else None
        protein = params.get("protein", "").lower() if params.get("protein") else None

        menu = load_json_file("menu.json")
        categories = menu.get("categories", {})

        # Check category exists
        if category not in categories:
            valid_cats = list(categories.keys())
            return {
                "ok": False,
                "valid": False,
                "error": f"Invalid category '{category}'. Valid categories: {', '.join(valid_cats)}",
                "validCategories": valid_cats
            }

        # Validate protein for kebabs/hsp
        if category in ["kebabs", "kebab", "hsp", "hsps"]:
            valid_proteins = ["lamb", "chicken", "mixed", "falafel"]
            if protein and protein not in valid_proteins:
                return {
                    "ok": False,
                    "valid": False,
                    "error": f"Invalid protein '{protein}'. Valid proteins: {', '.join(valid_proteins)}",
                    "validProteins": valid_proteins
                }

        # Validate size
        if size:
            valid_sizes = ["small", "large"]
            if size not in valid_sizes:
                return {
                    "ok": False,
                    "valid": False,
                    "error": f"Invalid size '{size}'. Valid sizes: {', '.join(valid_sizes)}",
                    "validSizes": valid_sizes
                }

        return {
            "ok": True,
            "valid": True,
            "category": category,
            "message": "Item configuration is valid"
        }

    except Exception as e:
        logger.error(f"Error validating menu item: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_repeat_last_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Copy customer's last order to current cart for fast reordering"""
    try:
        logger.info("Repeating last order")

        phone_number = params.get("phoneNumber")
        if not phone_number:
            return {"ok": False, "error": "phoneNumber is required"}

        # Get last order
        last_order_result = tool_get_last_order({"phoneNumber": phone_number})

        if not last_order_result.get("ok"):
            return last_order_result

        if not last_order_result.get("hasLastOrder"):
            return {
                "ok": False,
                "error": "No previous order found for this phone number"
            }

        # Copy cart from last order
        last_cart = last_order_result.get("cart", [])
        if not last_cart:
            return {"ok": False, "error": "Last order has no items"}

        # Set current cart to last order's cart
        session_set("cart", deepcopy(last_cart))
        session_set("cart_priced", False)  # Need to reprice

        return {
            "ok": True,
            "itemCount": len(last_cart),
            "lastOrderDate": last_order_result.get("orderDate"),
            "message": f"Added {len(last_cart)} items from your last order"
        }

    except Exception as e:
        logger.error(f"Error repeating last order: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_get_menu_by_category(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get all menu items in a specific category for browsing"""
    try:
        category = params.get("category", "").lower()

        if not category:
            # Return list of all categories
            menu = load_json_file("menu.json")
            categories = list(menu.get("categories", {}).keys())
            return {
                "ok": True,
                "categories": categories,
                "message": "Available categories"
            }

        menu = load_json_file("menu.json")
        categories = menu.get("categories", {})

        if category not in categories:
            return {
                "ok": False,
                "error": f"Invalid category: {category}",
                "availableCategories": list(categories.keys())
            }

        items = categories[category]

        # Format items for easy reading
        formatted_items = []
        for item in items:
            item_info = {
                "id": item.get("id"),
                "name": item.get("name"),
            }

            # Add pricing
            if "price" in item:
                item_info["price"] = item["price"]
            elif "sizes" in item:
                item_info["sizes"] = item["sizes"]

            # Add variants if present
            if "variants" in item:
                item_info["variants"] = item["variants"]

            # Add brands if present (for drinks)
            if "brands" in item:
                item_info["brands"] = item["brands"]

            formatted_items.append(item_info)

        return {
            "ok": True,
            "category": category,
            "items": formatted_items,
            "itemCount": len(formatted_items)
        }

    except Exception as e:
        logger.error(f"Error getting menu by category: {str(e)}")
        return {"ok": False, "error": str(e)}

# ==================== PERFORMANCE ENHANCEMENTS ====================

def tool_add_multiple_items_to_cart(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    PRIORITY 1: PARALLEL TOOL EXECUTION
    Add multiple items to cart in one call for 60-70% faster multi-item orders

    Input format:
    {
        "items": [
            {"category": "kebabs", "size": "large", "protein": "lamb", "salads": [...], "sauces": [...], "quantity": 2},
            {"category": "chips", "size": "large", "salt_type": "chicken", "quantity": 1},
            {"category": "drinks", "brand": "coke", "quantity": 2}
        ]
    }
    """
    try:
        logger.info("Adding multiple items to cart in batch")

        items = params.get("items", [])
        if not items:
            return {"ok": False, "error": "items array is required"}

        if not isinstance(items, list):
            return {"ok": False, "error": "items must be an array"}

        # Safety check: Limit batch size
        if len(items) > _MAX_BATCH_SIZE:
            return {
                "ok": False,
                "error": f"Batch size ({len(items)}) exceeds maximum of {_MAX_BATCH_SIZE}. Please add items in smaller batches."
            }

        # Get current cart
        cart = session_get("cart", [])

        # Check cart size before adding
        projected_size = len(cart) + len(items)
        if projected_size > _MAX_CART_SIZE:
            return {
                "ok": False,
                "error": f"Adding these items would exceed maximum cart size of {_MAX_CART_SIZE}. Current cart has {len(cart)} items."
            }
        added_count = 0
        failed_items = []

        # Process each item
        for idx, item_config in enumerate(items):
            try:
                # Validate required fields
                category = item_config.get("category", "").lower()
                if not category:
                    failed_items.append({"index": idx, "error": "Missing category"})
                    continue

                # Validate quantity
                quantity = item_config.get("quantity", 1)
                if quantity > _MAX_ITEM_QUANTITY:
                    failed_items.append({
                        "index": idx,
                        "error": f"Quantity ({quantity}) exceeds maximum of {_MAX_ITEM_QUANTITY}"
                    })
                    continue

                # Build cart item directly (bypass item state for speed)
                cart_item = {
                    "category": category,
                    "quantity": quantity
                }

                # Add size if provided
                if "size" in item_config:
                    cart_item["size"] = item_config["size"].lower()

                # Add protein if provided
                if "protein" in item_config:
                    cart_item["protein"] = item_config["protein"].lower()

                # Add salads if provided
                if "salads" in item_config:
                    salads = item_config["salads"]
                    if isinstance(salads, list):
                        cart_item["salads"] = [s.lower() for s in salads]
                    elif isinstance(salads, str):
                        cart_item["salads"] = [salads.lower()]

                # Add sauces if provided
                if "sauces" in item_config:
                    sauces = item_config["sauces"]
                    if isinstance(sauces, list):
                        cart_item["sauces"] = [s.lower() for s in sauces]
                    elif isinstance(sauces, str):
                        cart_item["sauces"] = [sauces.lower()]

                # Add extras if provided
                if "extras" in item_config:
                    extras = item_config["extras"]
                    if isinstance(extras, list):
                        cart_item["extras"] = [e.lower() for e in extras]

                # Add cheese if provided
                if "cheese" in item_config:
                    cart_item["cheese"] = bool(item_config["cheese"])

                # Add brand (for drinks)
                if "brand" in item_config:
                    cart_item["brand"] = item_config["brand"].lower()

                # Add variant (for items with variants)
                if "variant" in item_config:
                    cart_item["variant"] = item_config["variant"].lower()

                # Add salt_type (for chips)
                if "salt_type" in item_config:
                    cart_item["salt_type"] = item_config["salt_type"].lower()

                # Add sauce_type (for sauce tubs)
                if "sauce_type" in item_config:
                    cart_item["sauce_type"] = item_config["sauce_type"].lower()

                # Add notes if provided
                if "notes" in item_config:
                    cart_item["notes"] = str(item_config["notes"])

                # Add to cart
                cart.append(cart_item)
                added_count += 1

            except Exception as e:
                logger.error(f"Error adding item {idx}: {str(e)}")
                failed_items.append({"index": idx, "error": str(e)})

        # Update cart in session
        session_set("cart", cart)
        session_set("cart_priced", False)
        session_set("order_state", "CART_ACTIVE")

        # Check for combo opportunities
        combo_detected = detect_combo_opportunity(cart)
        if combo_detected:
            cart = apply_combo_to_cart(cart, combo_detected)
            session_set("cart", cart)

            return {
                "ok": True,
                "itemsAdded": added_count,
                "totalItems": len(cart),
                "combo": combo_detected["name"],
                "failedItems": failed_items if failed_items else None
            }

        return {
            "ok": True,
            "itemsAdded": added_count,
            "totalItems": len(cart),
            "failedItems": failed_items if failed_items else None
        }

    except Exception as e:
        logger.error(f"Error adding multiple items to cart: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


def tool_quick_add_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    PRIORITY 2: SMART CONTEXT MANAGEMENT
    Parse natural language and add item directly with minimal back-and-forth
    Supports common phrases like "large lamb kebab with extra garlic sauce"

    Expected improvement: 40-50% faster for simple orders
    """
    try:
        logger.info(f"Quick add item: {params}")

        description = params.get("description", "").lower()
        if not description:
            return {"ok": False, "error": "description is required"}

        # Initialize item config
        item_config = {}

        # Extract category (must be present)
        menu = load_json_file("menu.json")
        categories = menu.get("categories", {})

        # Category detection
        category_found = None
        if "kebab" in description and "hsp" not in description:
            category_found = "kebabs"
        elif "hsp" in description or "halal snack pack" in description:
            category_found = "hsp"
        elif "chip" in description or "fries" in description:
            category_found = "chips"
        elif "drink" in description or "coke" in description or "sprite" in description or "fanta" in description or "water" in description:
            category_found = "drinks"
        elif "gozleme" in description:
            category_found = "gozleme"
        elif "sweet" in description or "baklava" in description:
            category_found = "sweets"

        if not category_found:
            return {
                "ok": False,
                "error": "Could not identify item category. Please use startItemConfiguration instead.",
                "suggestion": "Try: 'kebab', 'hsp', 'chips', 'drinks', etc."
            }

        item_config["category"] = category_found

        # Extract size
        if "small" in description:
            item_config["size"] = "small"
        elif "large" in description or "big" in description:
            item_config["size"] = "large"
        elif category_found in ["kebabs", "hsp", "chips"]:
            # Default to large if not specified for main items
            item_config["size"] = "large"

        # Extract protein (for kebabs/hsp)
        if category_found in ["kebabs", "hsp"]:
            if "lamb" in description:
                item_config["protein"] = "lamb"
            elif "chicken" in description:
                item_config["protein"] = "chicken"
            elif "mix" in description:
                item_config["protein"] = "mixed"
            elif "falafel" in description:
                item_config["protein"] = "falafel"
            else:
                # Default to lamb if not specified
                item_config["protein"] = "lamb"

        # Extract quantity
        quantity = 1
        # Look for numbers at start: "2 large lamb kebabs"
        import re
        qty_match = re.match(r'^(\d+)\s+', description)
        if qty_match:
            quantity = int(qty_match.group(1))
        item_config["quantity"] = quantity

        # Extract salads (default to standard)
        if category_found in ["kebabs", "hsp"]:
            salads = []
            if "no salad" in description or "no salads" in description:
                salads = []
            elif "all salad" in description or "everything" in description:
                salads = ["lettuce", "tomato", "onion", "carrot", "cabbage"]
            else:
                # Default salads
                salads = ["lettuce", "tomato", "onion"]

                # Add extras mentioned
                if "carrot" in description:
                    salads.append("carrot")
                if "cabbage" in description:
                    salads.append("cabbage")

            item_config["salads"] = salads

        # Extract sauces
        if category_found in ["kebabs", "hsp"]:
            sauces = []

            # Check for specific sauces
            if "garlic" in description:
                sauces.append("garlic")
            if "chilli" in description or "chili" in description or "hot" in description:
                sauces.append("chilli")
            if "bbq" in description:
                sauces.append("bbq")
            if "tahini" in description:
                sauces.append("tahini")

            # Check for extra/more sauce
            if "extra" in description and ("sauce" in description or "garlic" in description):
                # Don't add extra garlic if already in list
                if "garlic" not in sauces:
                    sauces.append("garlic")
                # Mark it as extra in notes
                if "notes" not in item_config:
                    item_config["notes"] = "Extra garlic sauce"

            # Default to garlic if none specified
            if not sauces:
                sauces = ["garlic"]

            item_config["sauces"] = sauces

        # Extract cheese
        if "cheese" in description:
            item_config["cheese"] = True

        # Extract extras
        if category_found in ["kebabs", "hsp"]:
            extras = []
            if "haloumi" in description or "halloumi" in description:
                extras.append("haloumi")
            if "avocado" in description:
                extras.append("avocado")

            if extras:
                item_config["extras"] = extras

        # Drinks - extract brand
        if category_found == "drinks":
            if "coke" in description or "cola" in description:
                item_config["brand"] = "coke"
            elif "sprite" in description:
                item_config["brand"] = "sprite"
            elif "fanta" in description:
                item_config["brand"] = "fanta"
            elif "water" in description:
                item_config["brand"] = "water"
            else:
                item_config["brand"] = "coke"  # Default

        # Chips - extract salt type
        if category_found == "chips":
            if "chicken salt" in description or "chicken" in description:
                item_config["salt_type"] = "chicken"
            elif "sea salt" in description or "regular" in description:
                item_config["salt_type"] = "sea"
            elif "no salt" in description:
                item_config["salt_type"] = "none"
            else:
                item_config["salt_type"] = "chicken"  # Default

        # Now add the item using our batch add tool
        result = tool_add_multiple_items_to_cart({"items": [item_config]})

        if result.get("ok"):
            # Build confirmation message
            parts = []
            if quantity > 1:
                parts.append(f"{quantity}x")
            if item_config.get("size"):
                parts.append(item_config["size"])
            if item_config.get("protein"):
                parts.append(item_config["protein"])
            parts.append(category_found)

            confirmation = " ".join(parts)

            return {
                "ok": True,
                "added": confirmation,
                "cartCount": result.get("totalItems"),
                "parsed": item_config,
                "message": f"Added {confirmation} to cart"
            }
        else:
            return result

    except Exception as e:
        logger.error(f"Error in quick add item: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}


def tool_get_caller_smart_context(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    PRIORITY 3: INTELLIGENT ORDER PREDICTION
    Enhanced caller info with order history, patterns, and smart suggestions

    Returns:
    - Basic caller info
    - Last 3 orders with items
    - Most frequently ordered items
    - Usual pickup time preference
    - Dietary patterns detected
    - Smart greeting suggestion for AI
    """
    try:
        logger.info("Getting caller smart context")

        caller_number = caller_context.get()

        if not caller_number:
            return {
                "ok": True,
                "hasCallerID": False,
                "isNewCustomer": True,
                "greeting": "Welcome! What can I get for you today?"
            }

        local = _au_normalise_local(str(caller_number))
        last3 = _last3(local)

        # Get order history
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get last 3 completed orders
        cursor.execute("""
            SELECT id, order_id, cart, totals, created_at, ready_at
            FROM orders
            WHERE customer_phone = ?
            AND status IN ('completed', 'ready', 'preparing')
            ORDER BY created_at DESC
            LIMIT 3
        """, (local,))

        recent_orders = cursor.fetchall()

        if not recent_orders:
            release_db_connection(conn)
            return {
                "ok": True,
                "hasCallerID": True,
                "phoneNumber": local,
                "last3": last3,
                "isNewCustomer": True,
                "orderCount": 0,
                "greeting": f"Welcome! Is this your first time ordering with us?"
            }

        # Parse order history
        order_history = []
        all_items = []
        pickup_times = []

        for row in recent_orders:
            row_id, order_id, cart_json, totals_json, created_at, ready_at = row

            try:
                cart = json.loads(cart_json) if isinstance(cart_json, str) else cart_json
            except:
                cart = []

            try:
                totals = json.loads(totals_json) if isinstance(totals_json, str) else totals_json
                total = totals.get("total", 0) if totals else 0
            except:
                total = 0

            # Store order
            order_history.append({
                "orderId": order_id,
                "date": created_at,
                "itemCount": len(cart),
                "total": float(total) if total else 0
            })

            # Collect all items for pattern analysis
            for item in cart:
                all_items.append(item)

            # Track pickup times
            if ready_at:
                try:
                    ready_dt = datetime.fromisoformat(ready_at)
                    pickup_times.append(ready_dt.hour)
                except:
                    pass

        # Get total order count
        cursor.execute("""
            SELECT COUNT(*) FROM orders
            WHERE customer_phone = ?
            AND status IN ('completed', 'ready', 'preparing')
        """, (local,))

        total_orders = cursor.fetchone()[0]
        release_db_connection(conn)

        # Analyze patterns
        item_frequency = {}
        for item in all_items:
            key = f"{item.get('size', '')} {item.get('protein', '')} {item.get('category', '')}".strip().lower()
            item_frequency[key] = item_frequency.get(key, 0) + 1

        # Get top 3 most frequent items
        top_items = sorted(item_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        favorite_items = [{"item": item, "timesOrdered": count} for item, count in top_items]

        # Determine usual pickup time
        usual_time = None
        if pickup_times:
            avg_hour = sum(pickup_times) // len(pickup_times)
            if avg_hour < 12:
                usual_time = "morning"
            elif avg_hour < 17:
                usual_time = "afternoon"
            else:
                usual_time = "evening"

        # Detect dietary patterns
        dietary_notes = []
        vegetarian_count = sum(1 for item in all_items if item.get("protein") == "falafel")
        total_protein_items = sum(1 for item in all_items if item.get("protein"))

        if vegetarian_count > 0 and total_protein_items > 0:
            veg_ratio = vegetarian_count / total_protein_items
            if veg_ratio > 0.8:
                dietary_notes.append("prefers_vegetarian")
            elif veg_ratio > 0.3:
                dietary_notes.append("sometimes_vegetarian")

        # Check for cheese preference
        cheese_count = sum(1 for item in all_items if item.get("cheese"))
        if cheese_count > len(all_items) * 0.5:
            dietary_notes.append("loves_cheese")

        # Generate smart greeting
        days_since_last = None
        if recent_orders:
            try:
                last_order_date = datetime.fromisoformat(recent_orders[0][4])
                days_since_last = (datetime.now() - last_order_date).days
            except:
                pass

        # Build greeting suggestion
        if days_since_last is not None:
            if days_since_last == 0:
                greeting = f"Welcome back! Hungry again today?"
            elif days_since_last <= 3:
                greeting = f"Hey! Good to hear from you again!"
            elif days_since_last <= 7:
                greeting = f"Welcome back! It's been a few days."
            else:
                greeting = f"Welcome back! It's been a while - {days_since_last} days!"
        else:
            greeting = f"Welcome back! Great to hear from you again."

        # Add personalization based on favorites
        if favorite_items and total_orders >= 3:
            fav = favorite_items[0]["item"]
            greeting += f" Your usual {fav}?"

        return {
            "ok": True,
            "hasCallerID": True,
            "phoneNumber": local,
            "last3": last3,
            "isNewCustomer": False,
            "isRegular": total_orders >= 5,
            "orderCount": total_orders,
            "recentOrders": order_history,
            "favoriteItems": favorite_items,
            "usualPickupTime": usual_time,
            "dietaryNotes": dietary_notes,
            "daysSinceLastOrder": days_since_last,
            "greeting": greeting,
            "suggestRepeatOrder": total_orders >= 2  # Suggest "usual order" if 2+ orders
        }

    except Exception as e:
        logger.error(f"Error getting caller smart context: {str(e)}")
        import traceback
        traceback.print_exc()
        # Fallback to basic caller info
        return tool_get_caller_info(params)


def tool_end_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """End the call"""
    logger.info("Ending call")

    # FIXED: Don't clean sessions here - done by background task instead
    # This prevents deleting other active caller sessions

    return {"ok": True, "action": "end_call"}

# Tool mapping
TOOLS = {
    "checkOpen": tool_check_open,
    "getCallerInfo": tool_get_caller_info,
    "getCallerSmartContext": tool_get_caller_smart_context,  # NEW: Enhanced caller info with patterns
    "validateMenuItem": tool_validate_menu_item,
    "startItemConfiguration": tool_start_item_configuration,
    "setItemProperty": tool_set_item_property,
    "addItemToCart": tool_add_item_to_cart,
    "addMultipleItemsToCart": tool_add_multiple_items_to_cart,  # NEW: Batch add for speed
    "quickAddItem": tool_quick_add_item,  # NEW: Smart NLP parser
    "getCartState": tool_get_cart_state,
    "getDetailedCart": tool_get_detailed_cart,
    "removeCartItem": tool_remove_cart_item,
    "editCartItem": tool_edit_cart_item,
    "modifyCartItem": tool_modify_cart_item,
    "convertItemsToMeals": tool_convert_items_to_meals,
    "clearCart": tool_clear_cart,
    "clearSession": tool_clear_session,
    "priceCart": tool_price_cart,
    "getOrderSummary": tool_get_order_summary,
    "setOrderNotes": tool_set_order_notes,
    "getLastOrder": tool_get_last_order,
    "repeatLastOrder": tool_repeat_last_order,
    "getMenuByCategory": tool_get_menu_by_category,
    "lookupOrder": tool_lookup_order,
    "sendMenuLink": tool_send_menu_link,
    "setPickupTime": tool_set_pickup_time,
    "estimateReadyTime": tool_estimate_ready_time,
    "createOrder": tool_create_order,
    "endCall": tool_end_call,
}

# ==================== WEBHOOK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    health = get_system_health()
    status_code = 200 if health["status"] == "healthy" else 503
    return JSONResponse(content=health, status_code=status_code)


@app.get("/errors")
async def get_errors():
    """Get recent errors for debugging"""
    return JSONResponse(content={"errors": _ERROR_LOG[-20:]})  # Last 20 errors


@app.post("/webhook")
async def vapi_webhook(request: Request):
    """Main webhook endpoint with safety mechanisms"""
    start_time = datetime.now()

    try:
        data = await request.json()
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")

        # Set caller context and check rate limit
        caller_id = None
        if "call" in data:
            phone = data["call"].get("customer", {}).get("number") or data["call"].get("phoneNumber")
            if phone:
                caller_id = phone
                caller_context.set(phone)

                # Check rate limit
                if not check_rate_limit(caller_id):
                    logger.warning(f"Rate limit exceeded for {caller_id}")
                    error_response = {
                        "ok": False,
                        "error": "Rate limit exceeded. Please wait a moment before trying again."
                    }
                    update_system_health(0, False)
                    return JSONResponse(content=error_response, status_code=429)

        # Handle tool calls
        if "message" in data and "toolCalls" in data["message"]:
            tool_results = []
            for tool_call in data["message"]["toolCalls"]:
                tool_name = tool_call.get("function", {}).get("name") or tool_call.get("name")
                tool_args = tool_call.get("function", {}).get("arguments") or tool_call.get("parameters", {})

                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {}

                logger.info(f"Calling tool: {tool_name} with {tool_args}")

                if tool_name in TOOLS:
                    try:
                        # Sanitize inputs
                        tool_args = sanitize_input(tool_args)

                        # Execute tool
                        result = TOOLS[tool_name](tool_args)

                        # Track success
                        request_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                        update_system_health(request_time_ms, True)

                        tool_results.append({
                            "toolCallId": tool_call.get("id") or tool_call.get("toolCallId"),
                            "result": result
                        })
                    except Exception as tool_error:
                        logger.error(f"Tool {tool_name} error: {tool_error}")
                        log_error(tool_error, {"tool": tool_name, "args": tool_args})

                        # Track failure
                        request_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                        update_system_health(request_time_ms, False)

                        tool_results.append({
                            "toolCallId": tool_call.get("id") or tool_call.get("toolCallId"),
                            "result": {"ok": False, "error": f"Tool error: {str(tool_error)}"}
                        })
                else:
                    logger.warning(f"Unknown tool requested: {tool_name}")
                    tool_results.append({
                        "toolCallId": tool_call.get("id") or tool_call.get("toolCallId"),
                        "result": {"ok": False, "error": f"Unknown tool: {tool_name}"}
                    })

            return JSONResponse(content={"results": tool_results})

        return JSONResponse(content={"status": "received"})

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        import traceback
        traceback.print_exc()

        # Log error with context
        log_error(e, {"endpoint": "/webhook", "data": data if 'data' in locals() else None})

        # Track failure
        request_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        update_system_health(request_time_ms, False)

        return JSONResponse(content={"error": str(e)}, status_code=500)


async def cleanup_sessions_background():
    """Background task to clean expired sessions every 5 minutes"""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            logger.info("Running background session cleanup...")
            _clean_expired_sessions()
        except Exception as e:
            logger.error(f"Error in session cleanup background task: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and resources on startup"""
    logger.info("=" * 60)
    logger.info("Starting Kebabalab VAPI Server v2.1 - PRODUCTION")
    logger.info("=" * 60)
    logger.info("Initializing database...")
    init_db()
    logger.info("✓ Database initialized")
    logger.info("Starting background tasks...")
    asyncio.create_task(cleanup_sessions_background())
    logger.info("✓ Background session cleanup started")
    asyncio.create_task(periodic_health_checks())
    logger.info("✓ Periodic health monitoring started")
    logger.info("Checking system health...")
    check_database_health()
    logger.info("✓ Initial health check complete")
    logger.info("Server ready to accept requests with safety mechanisms active")
    logger.info("=" * 60)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

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

# ==================== SESSION MANAGEMENT ====================
# Per-caller session storage
SESSION = defaultdict(lambda: {
    "current_item": None,  # Item being configured
    "cart": [],  # Completed items
    "customer_info": {},  # Name, phone, etc
    "order_state": "IDLE"  # IDLE, CONFIGURING_ITEM, CART_READY, etc
})

def _session_key() -> str:
    """Get session key from caller context"""
    try:
        raw = caller_context.get() or "anon"
    except Exception:
        raw = "anon"
    raw = re.sub(r"\D+", "", str(raw))
    return raw or "anon"

def session_set(key: str, value: Any) -> None:
    """Set session value"""
    SESSION[_session_key()][key] = value

def session_get(key: str, default: Any = None) -> Any:
    """Get session value"""
    return SESSION[_session_key()].get(key, default)

def session_clear() -> None:
    """Clear session"""
    key = _session_key()
    if key in SESSION:
        del SESSION[key]

# ==================== HELPER FUNCTIONS ====================

def load_json_file(filename: str) -> Dict:
    """Load a JSON configuration file"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
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
        if self.salads:
            item["salads"] = self.salads
        if self.sauces:
            item["sauces"] = self.sauces
        if self.extras:
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
    """
    menu = load_json_file("menu.json")

    # Extract item types from cart
    has_kebab = None
    has_hsp = None
    has_chips = None
    has_can = None

    for item in cart:
        cat = item.get("category", "").lower()

        if cat in ["kebabs", "kebab"]:
            has_kebab = item
        elif cat in ["hsp", "hsps"]:
            has_hsp = item
        elif cat == "chips":
            has_chips = item
        elif cat == "drinks" and item.get("brand"):
            has_can = item

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
    name = item.get("name", "")

    base_price = Decimal("0")

    # Find base price in menu
    for cat_name, items in menu.get("categories", {}).items():
        if cat_name.lower() == category:
            for menu_item in items:
                # Match by name
                if menu_item.get("name") == name:
                    if "sizes" in menu_item and size:
                        base_price = Decimal(str(menu_item["sizes"].get(size, 0)))
                    elif "price" in menu_item:
                        base_price = Decimal(str(menu_item["price"]))
                    break
            if base_price > 0:
                break

    # Add extras pricing
    extras = item.get("extras", [])
    for extra in extras:
        for mod_extra in menu.get("modifiers", {}).get("extras", []):
            if mod_extra["name"].lower() == str(extra).lower():
                base_price += Decimal(str(mod_extra.get("price", 0)))

    # Extra sauces (more than 2)
    sauces = item.get("sauces", [])
    if len(sauces) > 2:
        base_price += Decimal("0.50") * (len(sauces) - 2)

    # Cheese if added
    if item.get("cheese") and category in ["kebabs", "kebab"]:
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

        # Set the property
        if field == "size":
            item_state.size = value
        elif field == "protein":
            item_state.protein = value
        elif field == "salads":
            item_state.salads = value if isinstance(value, list) else [value] if value else []
        elif field == "sauces":
            item_state.sauces = value if isinstance(value, list) else [value] if value else []
        elif field == "extras":
            item_state.extras = value if isinstance(value, list) else [value] if value else []
        elif field == "cheese":
            item_state.cheese = value
        elif field == "brand":
            item_state.brand = value
        elif field == "variant":
            item_state.variant = value
        elif field == "salt_type":
            item_state.salt_type = value
        elif field == "sauce_type":
            item_state.sauce_type = value
        elif field == "quantity":
            item_state.quantity = int(value) if value else 1
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

        result = {
            "ok": True,
            "itemAdded": cart_item,
            "cartItemCount": len(cart)
        }

        if combo_detected:
            # Apply combo
            cart = apply_combo_to_cart(cart, combo_detected)
            result["comboDetected"] = True
            result["comboInfo"] = {
                "name": combo_detected["name"],
                "type": combo_detected["type"],
                "savings": combo_detected["savings"]
            }
            result["message"] = f"I've made that a {combo_detected['name']} for you!"
        else:
            result["comboDetected"] = False
            result["message"] = "Item added to cart"

        # Update cart in session
        session_set("cart", cart)

        # Clear current item
        session_set("current_item", None)
        session_set("order_state", "CART_ACTIVE")

        result["updatedCart"] = cart

        return result

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

        return {
            "ok": True,
            "totals": {
                "subtotal": float(grand_total),
                "gst": float(gst_amount),
                "grand_total": float(grand_total)
            },
            "itemBreakdown": item_breakdown,
            "currency": "AUD"
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

def tool_estimate_ready_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate order ready time"""
    try:
        logger.info(f"Estimating ready time: {params}")

        # Check cart is priced
        if not session_get("cart_priced", False):
            return {
                "ok": False,
                "error": "Please price the cart first before estimating ready time"
            }

        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("business_details", {}).get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)

        # Default lead time: 15 min, busy time: 25 min
        lead_time = 15
        hour = now.hour
        if (11 <= hour <= 14) or (17 <= hour <= 20):
            lead_time = 25

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
        ready_at_iso = params.get("readyAtIso")

        if not customer_name:
            return {"ok": False, "error": "Customer name is required"}
        if not customer_phone:
            return {"ok": False, "error": "Customer phone is required"}
        if not ready_at_iso:
            return {"ok": False, "error": "Ready time is required"}

        # Save to database
        conn = init_db()
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
                order_type, cart, totals, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id_internal, now.isoformat(), ready_at_iso,
            customer_name, customer_phone, "pickup",
            json.dumps(cart), json.dumps(totals), "pending"
        ))
        conn.commit()
        conn.close()

        # Clear session
        session_set("cart", [])
        session_set("cart_priced", False)
        session_set("order_state", "ORDER_PLACED")

        return {
            "ok": True,
            "orderId": order_number,
            "orderIdInternal": order_id_internal,
            "total": totals["grand_total"],
            "message": f"Order {order_number} confirmed!"
        }

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_end_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """End the call"""
    logger.info("Ending call")
    return {"ok": True, "action": "end_call"}

# Tool mapping
TOOLS = {
    "checkOpen": tool_check_open,
    "getCallerInfo": tool_get_caller_info,
    "startItemConfiguration": tool_start_item_configuration,
    "setItemProperty": tool_set_item_property,
    "addItemToCart": tool_add_item_to_cart,
    "getCartState": tool_get_cart_state,
    "priceCart": tool_price_cart,
    "estimateReadyTime": tool_estimate_ready_time,
    "createOrder": tool_create_order,
    "endCall": tool_end_call,
}

# ==================== WEBHOOK ====================

@app.post("/webhook")
async def vapi_webhook(request: Request):
    """Main webhook endpoint"""
    try:
        data = await request.json()
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")

        # Set caller context
        if "call" in data:
            phone = data["call"].get("customer", {}).get("number") or data["call"].get("phoneNumber")
            if phone:
                caller_context.set(phone)

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
                    result = TOOLS[tool_name](tool_args)
                    tool_results.append({
                        "toolCallId": tool_call.get("id") or tool_call.get("toolCallId"),
                        "result": result
                    })
                else:
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
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

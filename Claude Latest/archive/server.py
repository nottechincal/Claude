"""
VAPI Server for Kebabalab Phone Orders - FIXED VERSION
Handles tool calls from VAPI assistant via webhooks and returns structured responses

This server receives function calls from VAPI and executes the corresponding business logic.
Configure VAPI to send function calls to: https://your-domain.com/vapi/webhook
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
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
import time

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

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Kebabalab VAPI Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Context variable for storing caller information per request
caller_context: ContextVar[Optional[str]] = ContextVar('caller_context', default=None)

# -------------------- SESSION HELPERS (per-caller scratchpad) --------------------
SESSION = defaultdict(dict)

def _session_key() -> str:
    try:
        raw = caller_context.get() or "anon"
    except Exception:
        raw = "anon"
    raw = re.sub(r"\D+", "", str(raw))
    return raw or "anon"

def session_set(key: str, value: Any) -> None:
    SESSION[_session_key()][key] = value

def session_get(key: str, default: Any = None) -> Any:
    return SESSION[_session_key()].get(key, default)

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

# ---- AU number helper: localise to 04xxxxxxxx (for logic) ----
def _au_normalise_local(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    d = re.sub(r"\D+", "", s)
    if not d:
        return None
    # +61XXXXXXXXX -> 0XXXXXXXXX
    if d.startswith("61") and len(d) == 11:
        return "0" + d[2:]
    if s.startswith("+61") and len(d) == 11:  # "+61 4xx..." -> d == "614xxxxxxxx"
        return "0" + d[2:]
    # already local-ish
    if d.startswith("0") and len(d) == 10:
        return d
    return d  # fallback (we'll still use digits)

def _last3(d: Optional[str]) -> Optional[str]:
    """Get last 3 digits of a phone number"""
    if not d:
        return None
    dd = re.sub(r"\D+", "", d)
    return dd[-3:] if len(dd) >= 3 else None

def _last3_spaced(last3: Optional[str]) -> Optional[str]:
    """Space out last 3 digits: '596' -> '5 9 6'"""
    return " ".join(list(last3)) if last3 else None

def _last3_words(last3: Optional[str]) -> Optional[str]:
    """Convert last 3 digits to words: '596' -> 'five nine six'"""
    if not last3:
        return None
    map_ = {"0":"zero","1":"one","2":"two","3":"three","4":"four","5":"five","6":"six","7":"seven","8":"eight","9":"nine"}
    return " ".join(map_.get(ch, ch) for ch in last3)

def _last3_ssml(last3: Optional[str], pause_ms: int = 250) -> Optional[str]:
    """Create SSML for slow digit-by-digit reading of last 3 digits"""
    if not last3:
        return None
    parts = []
    for i, ch in enumerate(last3):
        parts.append(ch)
        if i < len(last3) - 1:
            parts.append(f'<break time="{pause_ms}ms"/>')
    return f"<speak>{''.join(parts)}</speak>"

def _display_spaced_local(d: Optional[str]) -> Optional[str]:
    if not d:
        return None
    d = re.sub(r"\D+", "", d)
    if len(d) == 10:
        return f"{d[:4]} {d[4:7]} {d[7:]}"  # 0423 680 596
    return d

# ---- E.164 for Twilio send ----
def _au_to_e164(mobile: str) -> str:
    """
    Normalise Australian numbers to E.164 for Twilio.
      0423680596   -> +61423680596
      +61 423 680 596 -> +61423680596
    Leaves already-E.164 numbers as-is. Returns input on parse failure.
    """
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

# ==================== TOOL IMPLEMENTATIONS ====================

def tool_check_open(params: Dict[str, Any]) -> Dict[str, Any]:
    """Check if shop is currently open"""
    try:
        logger.info("Checking if shop is open")
        hours = load_json_file("hours.json")
        tz = pytz.timezone(hours.get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)
        day_name = now.strftime("%a").lower()
        today_hours = hours.get("weekly", {}).get(day_name, [])
        is_open = False
        if today_hours:
            current_time = now.strftime("%H:%M")
            for time_range in today_hours:
                if "-" in time_range:
                    start, end = time_range.split("-")
                    if start == "00:00" and end == "23:59":
                        is_open = True
                        break
                    if start <= current_time <= end:
                        is_open = True
                        break
        result = {
            "ok": True,
            "isOpen": is_open,
            "currentTime": now.isoformat(),
            "dayOfWeek": day_name,
            "todayHours": ", ".join(today_hours) if today_hours else "closed"
        }
        logger.info(f"Shop is open: {is_open}")
        return result
    except Exception as e:
        logger.error(f"Error checking if shop is open: {str(e)}")
        return {"ok": False, "error": str(e), "isOpen": False}

def validate_menu_item(category: str, item_name: str = None, size: str = None, brand: str = None) -> Dict[str, Any]:
    """Validate if an item exists in the menu"""
    try:
        menu = load_json_file("menu.json")
        synonyms = menu.get("synonyms", {})
        
        # First, check if item_name is a synonym that maps to a full item name
        mapped_item_name = item_name
        if item_name and item_name.lower() in synonyms:
            mapped_name = synonyms[item_name.lower()]
            # Only use the mapped name if it's a valid menu item name
            for cat_name, category_items in menu.get("categories", {}).items():
                for menu_item in category_items:
                    if menu_item.get("name") == mapped_name:
                        mapped_item_name = mapped_name
                        break
        
        # Now validate with the (potentially mapped) item name
        if category not in menu.get("categories", {}):
            return {"valid": False, "error": f"Category '{category}' not found",
                    "available_categories": list(menu.get("categories", {}).keys())}
        
        category_items = menu["categories"][category]
        
        # Handle drinks with brands
        if category == "drinks" and brand:
            for item in category_items:
                if item.get("name") == "Soft Drink Can (375ml)":
                    available_brands = item.get("brands", [])
                    if brand.lower() not in [b.lower() for b in available_brands]:
                        return {"valid": False, "error": f"Brand '{brand}' not available",
                                "available_brands": available_brands}
                    return {"valid": True}
        
        # Handle extras
        if category == "extras" and mapped_item_name:
            for item in category_items:
                if item.get("name") == mapped_item_name:
                    return {"valid": True}
            return {"valid": False, "error": f"Item '{mapped_item_name}' not found in {category}",
                    "available_items": [item.get("name") for item in category_items]}
        
        # Handle sauce tubs
        if category == "sauce_tubs" and mapped_item_name:
            for item in category_items:
                if item.get("name") == "Sauce Tub":
                    available_sauces = item.get("available_sauces", [])
                    if mapped_item_name.lower() not in [s.lower() for s in available_sauces]:
                        return {"valid": False, "error": f"Sauce '{mapped_item_name}' not available",
                                "available_sauces": available_sauces}
                    return {"valid": True}
            return {"valid": False, "error": f"Sauce tubs not available"}
        
        # Handle regular items with names
        if mapped_item_name:
            for item in category_items:
                if item.get("name") == mapped_item_name:
                    # Check size if applicable
                    if size and "sizes" in item and size not in item["sizes"]:
                        return {"valid": False, "error": f"Size '{size}' not available for {mapped_item_name}",
                                "available_sizes": list(item["sizes"].keys())}
                    return {"valid": True}
            
            # If we didn't find the exact name, try to find partial matches
            for item in category_items:
                item_name_lower = item.get("name", "").lower()
                mapped_lower = mapped_item_name.lower()
                # Check if the requested item contains the menu item name or vice versa
                if mapped_lower in item_name_lower or item_name_lower in mapped_lower:
                    # Check size if applicable
                    if size and "sizes" in item and size not in item["sizes"]:
                        return {"valid": False, "error": f"Size '{size}' not available for {item.get('name')}",
                                "available_sizes": list(item["sizes"].keys())}
                    return {"valid": True, "matched_item": item.get("name")}
            
            return {"valid": False, "error": f"Item '{mapped_item_name}' not found in {category}",
                    "available_items": [item.get("name") for item in category_items]}
        
        # If no item name provided, just check if category is valid
        return {"valid": True}
    except Exception as e:
        logger.error(f"Error validating menu item: {str(e)}")
        return {"valid": False, "error": str(e)}

def tool_get_menu(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get menu information"""
    try:
        logger.info("Getting menu information")
        menu = load_json_file("menu.json")
        category_filter = params.get("category")
        result = {
            "ok": True,
            "currency": menu.get("currency", "AUD"),
            "categories": list(menu.get("categories", {}).keys()),
            "modifiers": menu.get("modifiers", {}),
            "defaults": menu.get("defaults", {}),
            "synonyms": menu.get("synonyms", {})
        }
        if category_filter:
            if category_filter in menu.get("categories", {}):
                result["items"] = menu["categories"][category_filter]
            else:
                result["ok"] = False
                result["error"] = f"Category '{category_filter}' not found"
        else:
            result["menu"] = menu
        return result
    except Exception as e:
        logger.error(f"Error getting menu: {str(e)}")
        return {"ok": False, "error": str(e)}

def tool_get_caller_info(params: Dict[str, Any]) -> Dict[str, Any]:
    """Get caller info silently. Return fields to support clear last-3 confirmation and optional full-read."""
    try:
        logger.info("Getting caller information")
        caller_number = caller_context.get()
        logger.info(f"Caller number: {caller_number}")
        if caller_number:
            local = _au_normalise_local(str(caller_number))
            local = local if (local and local.startswith("0") and len(local) == 10) else (local or str(caller_number))
            last3 = _last3(local)
            last3_sp = _last3_spaced(last3)
            last3_words = _last3_words(last3)
            last3_ssml = _last3_ssml(last3, pause_ms=250)
            display = _display_spaced_local(local)
            return {
                "ok": True,
                "hasCallerID": True,
                "phoneNumber": local,        # for tools and createOrder; do not auto-say
                "last3": last3,              # "596"
                "last3_spaced": last3_sp,    # "5 9 6"
                "last3_words": last3_words,  # "five nine six"
                "last3_ssml": last3_ssml,    # SSML for slow digits
                "display": display           # "0423 680 596" (say only if asked)
            }
        return {
            "ok": True,
            "hasCallerID": False,
            "phoneNumber": None,
            "last3": None,
            "last3_spaced": None,
            "last3_words": None,
            "last3_ssml": None,
            "display": None,
        }
    except Exception as e:
        logger.error(f"Error getting caller info: {str(e)}")
        return {
            "ok": False,
            "error": str(e),
            "hasCallerID": False,
            "phoneNumber": None,
            "last3": None,
            "last3_spaced": None,
            "last3_words": None,
            "last3_ssml": None,
            "display": None,
        }

def tool_price_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate order pricing with server-side validation for kebab/HSP size+protein."""
    try:
        logger.info(f"Calculating order price with params: {json.dumps(params, indent=2)}")
        cart = params.get("cart", [])
        if not cart:
            logger.error("Cart is empty")
            return {"ok": False, "error": "Cart is empty"}

        # ---- Hard validation: kebabs/HSPs require size + protein ----
        for idx, item in enumerate(cart):
            # Skip combo items for validation
            if item.get("category") == "combos":
                continue
                
            # Ensure item is a dictionary
            if not isinstance(item, dict):
                logger.error(f"Cart item {idx} is not a dictionary: {item}")
                return {"ok": False, "error": f"Invalid cart item at position {idx+1}. Each item should be an object."}
                
            cat = (item.get("category") or "").lower()
            size = item.get("size")
            protein = item.get("protein")
            name = item.get("name", "")
            
            logger.info(f"Validating item {idx}: category={cat}, name={name}, size={size}, protein={protein}")
            
            if cat in {"kebabs", "kebab", "hsp", "hsps"}:
                if not size:
                    return {"ok": False, "error": f"Line {idx+1}: kebab/HSP requires a size (small/large)."}
                if not protein:
                    # Try to infer protein from name if possible
                    name_lower = name.lower()
                    if "chicken" in name_lower:
                        protein = "chicken"
                    elif "lamb" in name_lower:
                        protein = "lamb"
                    elif "mix" in name_lower:
                        protein = "mix"
                    elif "falafel" in name_lower:
                        protein = "falafel"
                    else:
                        return {"ok": False, "error": f"Line {idx+1}: kebab/HSP requires a protein (lamb/chicken/mix/falafel)."}
                    
                    # Update the item with inferred protein
                    item["protein"] = protein
                    logger.info(f"Inferred protein: {protein}")

        menu = load_json_file("menu.json")
        gst_rate = Decimal(os.getenv("GST_RATE", "0.10"))

        subtotal = Decimal("0")
        item_breakdown = []

        for idx, item in enumerate(cart):
            logger.info(f"Processing item {idx}: {item}")

            # Ensure item is a dictionary
            if not isinstance(item, dict):
                logger.error(f"Cart item {idx} is not a dictionary: {item}")
                return {"ok": False, "error": f"Invalid cart item at position {idx+1}. Each item should be an object."}

            quantity = item.get("quantity", 1)
            category = item.get("category", "")
            size = item.get("size", "")
            protein = item.get("protein", "")
            name = item.get("name", "")

            # Handle combo items
            if category == "combos":
                # For combo items, we need to calculate the price based on the individual items
                combo_items = item.get("combo_items", [])
                combo_price_adjustment = item.get("price_adjustment", 0)
                
                combo_total = Decimal("0")
                for combo_item in combo_items:
                    # Find the matching item in the cart
                    for cart_item in cart:
                        if item_matches_pattern(cart_item, combo_item):
                            # Calculate price for this item
                            item_price = calculate_item_price(cart_item, menu)
                            combo_total += item_price
                            break
                
                # Apply combo discount
                combo_total += Decimal(str(combo_price_adjustment))
                
                line_total = combo_total * Decimal(str(quantity))
                subtotal += line_total
                
                # Friendly description
                desc_parts = []
                if size:
                    desc_parts.append(size.capitalize())
                if protein:
                    desc_parts.append(protein.capitalize())
                if name:
                    desc_parts.append(name)
                
                item_breakdown.append({
                    "line": idx,
                    "description": " ".join(desc_parts),
                    "price": float(combo_total),
                    "quantity": quantity,
                    "lineTotal": float(line_total),
                    "isCombo": True
                })
                continue
            
            # Find base price for regular items
            item_price = calculate_item_price(item, menu)
            
            logger.info(f"Found item price: {item_price}")

            modifiers = item.get("modifiers", {})
            salads = item.get("salads", modifiers.get("salads", [])) or []
            sauces = item.get("sauces", modifiers.get("sauces", [])) or []
            extras = item.get("extras", modifiers.get("extras", [])) or []

            # Handle special categories
            if category == "extras":
                for extra_item in menu.get("categories", {}).get("extras", []):
                    if extra_item.get("name") == name:
                        item_price = Decimal(str(extra_item.get("price", 0)))
                        break
            
            if category == "sauce_tubs":
                # All sauce tubs are $1.00
                item_price = Decimal("1.00")

            # Extras pricing
            for extra in extras:
                for mod_extra in menu.get("modifiers", {}).get("extras", []):
                    if mod_extra["name"].lower() == str(extra).lower():
                        item_price += Decimal(str(mod_extra.get("price", 0)))

            # Extra sauces beyond 2 (mixed in)
            if len(sauces) > 2:
                item_price += Decimal("0.50") * (len(sauces) - 2)

            line_total = item_price * Decimal(str(quantity))
            subtotal += line_total

            # Friendly description
            desc_parts = []
            if size:
                desc_parts.append(size.capitalize())
            if protein:
                desc_parts.append(protein.capitalize())
            if name:
                desc_parts.append(name)
            elif category:
                desc_parts.append(category.upper())

            item_breakdown.append({
                "line": idx,
                "description": " ".join(desc_parts),
                "price": float(item_price),
                "quantity": quantity,
                "lineTotal": float(line_total),
                "salads": salads,
                "sauces": sauces,
                "extras": extras,
            })

        grand_total = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        gst_amount = ((subtotal * gst_rate) / (Decimal("1") + gst_rate)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # remember pricing (for time estimate gate)
        try:
            session_set("last_totals", {
                "subtotal": float(grand_total),
                "gst": float(gst_amount),
                "grand_total": float(grand_total)
            })
            session_set("cart_priced", True)
        except Exception:
            pass

        result = {
            "ok": True,
            "totals": {
                "subtotal": float(grand_total),
                "gst": float(gst_amount),
                "grand_total": float(grand_total)
            },
            "itemBreakdown": item_breakdown,
            "currency": "AUD"
        }
        logger.info(f"Price calculation successful: {result}")
        return result

    except Exception as e:
        import traceback
        logger.error(f"Error calculating price: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def calculate_item_price(item: Dict, menu: Dict) -> Decimal:
    """Calculate the price of a single item"""
    category = item.get("category", "")
    name = item.get("name", "")
    size = item.get("size", "")
    
    item_price = Decimal("0")
    found_item = False
    
    # First try exact match
    for cat_name, items in menu.get("categories", {}).items():
        if cat_name == category:
            for menu_item in items:
                if menu_item.get("name") == name:
                    found_item = True
                    if "sizes" in menu_item and size:
                        item_price = Decimal(str(menu_item["sizes"].get(size, 0)))
                    elif "price" in menu_item:
                        item_price = Decimal(str(menu_item["price"]))
                    break
            if found_item:
                break
    
    # If not found, try synonym mapping
    if not found_item and name:
        synonyms = menu.get("synonyms", {})
        if name.lower() in synonyms:
            mapped_name = synonyms[name.lower()]
            for cat_name, items in menu.get("categories", {}).items():
                if cat_name == category:
                    for menu_item in items:
                        if menu_item.get("name") == mapped_name:
                            found_item = True
                            if "sizes" in menu_item and size:
                                item_price = Decimal(str(menu_item["sizes"].get(size, 0)))
                            elif "price" in menu_item:
                                item_price = Decimal(str(menu_item["price"]))
                            break
                if found_item:
                    break
    
    # If still not found, try partial match
    if not found_item and name:
        for cat_name, items in menu.get("categories", {}).items():
            if cat_name == category:
                for menu_item in items:
                    menu_item_name = menu_item.get("name", "").lower()
                    name_lower = name.lower()
                    if name_lower in menu_item_name or menu_item_name in name_lower:
                        found_item = True
                        if "sizes" in menu_item and size:
                            item_price = Decimal(str(menu_item["sizes"].get(size, 0)))
                        elif "price" in menu_item:
                            item_price = Decimal(str(menu_item["price"]))
                        break
            if found_item:
                break
    
    if not found_item:
        logger.error(f"Could not find item: {name} in category {category}")
        return Decimal("0")
    
    return item_price

def tool_estimate_ready_time(params: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate when order will be ready"""
    try:
        logger.info(f"Estimating ready time with params: {json.dumps(params, indent=2)}")
        rules = load_json_file("rules.json")
        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)

        # gate to ensure pricing/total happens first
        cart_priced = True
        try:
            cart_priced = session_get("cart_priced", False)
        except Exception:
            cart_priced = True
        if not cart_priced:
            return {
                "ok": False,
                "needPricing": True,
                "message": "Please call priceOrder with the complete cart and announce the total before estimating pickup time."
            }

        # Determine lead time based on time of day
        lead_time = rules.get("lead_time_minutes", {}).get("default", 15)
        hour = now.hour
        if (11 <= hour <= 14) or (17 <= hour <= 20):
            lead_time = rules.get("lead_time_minutes", {}).get("busy", 25)

        # Calculate earliest ready time
        earliest_ready = now + timedelta(minutes=lead_time)

        # Parse requested time
        requested_time_str = (params.get("requestedTime") or "").strip()
        logger.info(f"Parsing time request: '{requested_time_str}'")

        minutes_value, is_relative, absolute_dt = parse_time_request(requested_time_str, now)

        # Fallbacks for common phrases the parser might miss
        if is_relative and minutes_value is None and requested_time_str:
            s = requested_time_str.lower()
            if ("half an hour" in s) or ("half hour" in s):
                minutes_value = 30
            elif re.search(r"\ban hour\b", s) or re.search(r"\babout an hour\b", s):
                minutes_value = 60

        logger.info(f"Parsed - minutes: {minutes_value}, is_relative: {is_relative}, absolute: {absolute_dt}")

        # Response style mirrors user
        if is_relative and minutes_value:
            requested_ready = now + timedelta(minutes=minutes_value)
            if requested_ready >= earliest_ready:
                ready_time = requested_ready
                s = requested_time_str.lower()
                about_flag = "about" in s or "approx" in s or "around" in s
                if minutes_value % 60 == 0 and minutes_value >= 60:
                    hours = minutes_value // 60
                    hours_phrase = "1 hour" if hours == 1 else f"{hours} hours"
                    message = f"Your order will be ready {'in about ' if about_flag else 'in '}{hours_phrase}"
                else:
                    message = f"Your order will be ready {'in about ' if about_flag else 'in '}{minutes_value} minutes"
            else:
                ready_time = earliest_ready
                earliest_minutes = int((earliest_ready - now).total_seconds() / 60)
                message = f"The earliest is in about {earliest_minutes} minutes. Is that okay?"

        elif not is_relative and absolute_dt:
            if absolute_dt.tzinfo is None:
                requested_ready = tz.localize(absolute_dt)
            else:
                requested_ready = absolute_dt.astimezone(tz)

            if requested_ready >= earliest_ready:
                ready_time = requested_ready
                time_display = format_time_for_speech(ready_time)
                message = f"Your order will be ready at {time_display}"
            else:
                ready_time = earliest_ready
                time_display = format_time_for_speech(ready_time)
                message = f"The earliest pickup time is {time_display}. Is that okay?"

        else:
            ready_time = earliest_ready
            earliest_minutes = int((earliest_ready - now).total_seconds() / 60)
            message = f"Your order will be ready in about {earliest_minutes} minutes"

        ready_time_display = format_time_for_speech(ready_time)
        minutes_until = int((ready_time - now).total_seconds() / 60)

        logger.info(f"Final message: {message}")

        result = {
            "ok": True,
            "readyAtIso": ready_time.isoformat(),
            "readyAt": ready_time_display,
            "readyAtMinutes": minutes_until,
            "leadTimeMinutes": lead_time,
            "earliestReadyIso": earliest_ready.isoformat(),
            "earliestReadyMinutes": int((earliest_ready - now).total_seconds() / 60),
            "message": message
        }
        logger.info(f"Ready time estimation successful: {result}")
        return result
    except Exception as e:
        import traceback
        logger.error(f"Error estimating ready time: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def format_time_for_speech(dt):
    """Format datetime for natural TTS speech"""
    hour = dt.hour
    minute = dt.minute
    if hour == 0:
        hour_12 = 12; period = "AM"
    elif hour < 12:
        hour_12 = hour; period = "AM"
    elif hour == 12:
        hour_12 = 12; period = "PM"
    else:
        hour_12 = hour - 12; period = "PM"
    if minute == 0:
        return f"{hour_12} {period}"
    elif minute < 10:
        return f"{hour_12} oh {minute} {period}"
    else:
        return f"{hour_12} {minute} {period}"

def parse_time_request(requested_time_str: str, now: datetime) -> tuple:
    """
    Parse customer's time request and return (minutes, is_relative, parsed_datetime)
    - Supports: "in 20 minutes", "in 2 hours", "in an hour", "in half an hour",
                "at 6 pm", "6:30 pm", "19:10", "as soon as possible"
    """
    if not requested_time_str:
        return None, True, None
    s = requested_time_str.lower().strip()
    if "as soon as possible" in s or s == "asap":
        return None, True, None
    if s.startswith("in "):
        if "half an hour" in s or "half hour" in s:
            return 30, True, None
        if re.search(r"\bin an hour\b", s) or re.search(r"\ban hour\b", s):
            return 60, True, None
        nums = re.findall(r"\d+", s)
        if nums:
            value = int(nums[0])
            if "hour" in s:
                return value * 60, True, None
            return value, True, None
    if "half an hour" in s or "half hour" in s:
        return 30, True, None
    if re.search(r"\ban hour\b", s) or re.search(r"\babout an hour\b", s):
        return 60, True, None
    if re.match(r'^\d+\s*(min|mins|minute|minutes)\b', s):
        return int(re.findall(r"\d+", s)[0]), True, None
    if re.match(r'^\d+\s*(h|hr|hrs|hour|hours)\b', s):
        return int(re.findall(r"\d+", s)[0]) * 60, True, None
    try:
        t = s.replace("at ", "").strip().upper()
        for fmt in ["%I:%M %p", "%I %p", "%I:%M%p", "%I%p"]:
            try:
                p = datetime.strptime(t, fmt)
                dt = now.replace(hour=p.hour, minute=p.minute, second=0, microsecond=0)
                if dt < now:
                    dt += timedelta(days=1)
                return None, False, dt
            except:
                pass
        for fmt in ["%H:%M", "%H"]:
            try:
                p = datetime.strptime(t, fmt)
                dt = now.replace(hour=p.hour, minute=p.minute, second=0, microsecond=0)
                if dt < now:
                    dt += timedelta(days=1)
                return None, False, dt
            except:
                pass
    except:
        pass
    try:
        dt = datetime.fromisoformat(requested_time_str.replace("Z", "+00:00"))
        return None, False, dt
    except:
        pass
    return None, True, None

def tool_create_order(params: Dict[str, Any]) -> Dict[str, Any]:
    """Create and save order"""
    try:
        logger.info(f"Creating order with params: {json.dumps(params, indent=2)}")
        cart = params.get("cart")
        totals = params.get("totals")
        contact = params.get("contact", {})
        ready_at_iso = params.get("readyAtIso")

        if not cart:
            return {"ok": False, "error": "Cart is required"}
        if not totals:
            return {"ok": False, "error": "Totals are required"}
        if not contact.get("phone"):
            return {"ok": False, "error": "Customer phone is required"}
        if not contact.get("name"):
            return {"ok": False, "error": "Customer name is required"}
        if not ready_at_iso:
            return {"ok": False, "error": "Ready time is required"}

        # SAFETY CHECK: Ensure we're not using the shop's number as customer number
        shop_number = os.getenv("SHOP_ORDER_TO", "0423680596")
        normalized_shop = _au_normalise_local(shop_number)
        customer_phone = contact.get("phone")
        normalized_customer = _au_normalise_local(customer_phone)
        
        if normalized_customer == normalized_shop:
            return {
                "ok": False, 
                "error": f"Cannot use shop number ({shop_number}) as customer phone number. Please provide the customer's actual phone number."
            }

        conn = init_db()
        cursor = conn.cursor()

        today = datetime.now().strftime("%Y%m%d")
        cursor.execute("SELECT COUNT(*) FROM orders WHERE order_id LIKE ?", (f"{today}-%",))
        count = cursor.fetchone()[0]
        order_id_internal = f"{today}-{(count + 1):03d}"
        order_number_display = f"{(count + 1):03d}"

        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("timezone", "Australia/Melbourne"))
        now = datetime.now(tz)

        try:
            ready_dt = datetime.fromisoformat(ready_at_iso.replace("Z", "+00:00"))
            if ready_dt.tzinfo is None:
                ready_dt = tz.localize(ready_dt)
            ready_display = format_time_for_speech(ready_dt)
        except:
            ready_display = ready_at_iso

        cursor.execute("""
            INSERT INTO orders (
                order_id, created_at, ready_at, customer_name, customer_phone,
                order_type, delivery_address, cart, totals, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id_internal, now.isoformat(), ready_at_iso,
            contact.get("name"), contact.get("phone"),
            contact.get("order_type", "pickup"), contact.get("address"),
            json.dumps(cart), json.dumps(totals), "pending", params.get("notes")
        ))
        conn.commit()
        conn.close()

        result = {
            "ok": True,
            "orderId": order_number_display,
            "orderIdInternal": order_id_internal,
            "readyAt": ready_display,
            "readyAtIso": ready_at_iso,
            "customerPhone": contact.get("phone"),
            "total": totals.get("grand_total"),
            "message": f"Order confirmed! Your order number is {order_number_display}"
        }

        # auto-notify shop if Twilio env set
        try:
            if os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and (os.getenv("TWILIO_FROM") or os.getenv("TWILIO_PHONE_NUMBER")) and os.getenv("SHOP_ORDER_TO"):
                notify_payload = {
                    "orderId": order_number_display,
                    "cart": cart,
                    "totals": totals,
                    "readyAtIso": ready_at_iso,
                    "contact": {"name": contact.get("name"), "phone": contact.get("phone")},
                    "order_type": contact.get("order_type", "pickup")
                }
                notify_res = tool_notify_shop(notify_payload)
                result["shopNotified"] = notify_res.get("ok", False)
                if not notify_res.get("ok"):
                    result["shopNotifyError"] = notify_res.get("error")
        except Exception as _e:
            result["shopNotified"] = False
            result["shopNotifyError"] = str(_e)

        logger.info(f"Order created successfully: {result}")
        return result

    except Exception as e:
        import traceback
        logger.error(f"Error creating order: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_send_receipt(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send SMS receipt to customer (requires consent:true; normalises numbers)"""
    if not bool(params.get("consent", False)):
        return {"ok": False, "error": "SMS not sent: explicit customer consent is required (consent=true)."}

    try:
        logger.info(f"Sending receipt with params: {json.dumps(params, indent=2)}")
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM") or os.getenv("TWILIO_PHONE_NUMBER")
        to_phone = params.get("toPhone")

        if not all([account_sid, auth_token, from_number, to_phone]):
            missing = []
            if not account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not from_number: missing.append("TWILIO_FROM or TWILIO_PHONE_NUMBER")
            if not to_phone: missing.append("toPhone parameter")
            return {"ok": False, "error": f"Missing configuration: {', '.join(missing)}"}
        
        # SAFETY CHECK: Prevent sending receipt to shop number
        shop_number = os.getenv("SHOP_ORDER_TO", "0423680596")
        normalized_shop = _au_normalise_local(shop_number)
        normalized_to = _au_normalise_local(to_phone)
        
        if normalized_to == normalized_shop:
            error_msg = f"🚨 BLOCKED: Cannot send receipt to shop number ({normalized_shop})! This should go to the CUSTOMER's phone. Use the phone number you collected during checkout."
            logger.error(error_msg)
            return {
                "ok": False, 
                "error": error_msg,
                "hint": "Use contact.phone from the customer contact info you collected"
            }

        order_id = params.get("orderId")
        cart = params.get("cart", [])
        totals = params.get("totals", {})
        ready_at_iso = params.get("readyAtIso")

        # If no order details, this might be a menu link request - redirect
        if not order_id or not ready_at_iso:
            return {"ok": False, "error": "Missing order details. Use sendMenuLink for menu requests.", "suggestion": "Use sendMenuLink({}) to send menu instead"}

        business = load_json_file("business.json")
        tz = pytz.timezone(business.get("timezone", "Australia/Melbourne"))
        ready_dt = datetime.fromisoformat(ready_at_iso.replace("Z", "+00:00"))
        if ready_dt.tzinfo is None:
            ready_dt = tz.localize(ready_dt)
        ready_display = format_time_for_speech(ready_dt)

        # Build detailed lines WITH salads/sauces/extras
        lines = []
        for idx, item in enumerate(cart, 1):
            qty = int(item.get("quantity", 1))
            size = item.get("size")
            protein = item.get("protein")
            name = item.get("name")
            salads = item.get("salads") or item.get("modifiers", {}).get("salads", [])
            sauces = item.get("sauces") or item.get("modifiers", {}).get("sauces", [])
            extras = item.get("extras") or item.get("modifiers", {}).get("extras", [])

            head = []
            if qty > 1: head.append(f"{qty}x")
            if size: head.append(size.capitalize())
            if protein: head.append(protein.capitalize())
            if name: head.append(name)
            lines.append(f"{idx}. {' '.join(head) if head else 'Item'}")

            if salads: lines.append(f"   Salads: {', '.join(salads)}")
            if sauces: lines.append(f"   Sauces: {', '.join(sauces)}")
            if extras: lines.append(f"   Extras: {', '.join(extras)}")

        message_body = f"""Thank you for your order!

Order: {order_id}
Pickup: {ready_display}

{chr(10).join(lines)}

Total: ${totals.get('grand_total', 0):.2f}

Kebabalab
1/99 Carlisle St, St Kilda
See you soon!"""

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=_au_to_e164(from_number),
            to=_au_to_e164(to_phone)
        )

        logger.info(f"Receipt sent to customer: {_au_to_e164(to_phone)}")
        return {"ok": True, "messageSid": message.sid, "sentTo": _au_to_e164(to_phone)}
    except Exception as e:
        import traceback
        logger.error(f"Error sending receipt: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_send_menu_link(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send SMS with menu link to customer. Auto-detects phone from caller context if not provided."""
    try:
        logger.info(f"Sending menu link with params: {json.dumps(params, indent=2)}")
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM") or os.getenv("TWILIO_PHONE_NUMBER")
        
        # Get phone number - from params or from caller context
        to_phone = params.get("toPhone")
        if not to_phone:
            # Try to get from caller context
            caller_number = caller_context.get()
            if caller_number:
                to_phone = _au_normalise_local(str(caller_number))
                logger.info(f"sendMenuLink using caller context phone: {to_phone}")
            else:
                return {"ok": False, "error": "No customer phone number available"}
        
        # SAFETY CHECK: Prevent sending to shop number
        shop_number = os.getenv("SHOP_ORDER_TO", "0423680596")
        normalized_shop = _au_normalise_local(shop_number)
        normalized_to = _au_normalise_local(to_phone)
        
        if normalized_to == normalized_shop:
            error_msg = f"🚨 BLOCKED: Cannot send menu to shop number ({normalized_shop})! This should go to the CUSTOMER's phone. Check your prompt instructions."
            logger.error(error_msg)
            return {
                "ok": False, 
                "error": error_msg,
                "hint": "Use the phone number from getCallerInfo.phoneNumber or ask the customer for their number"
            }

        # Check Twilio configuration
        if not all([account_sid, auth_token, from_number]):
            missing = []
            if not account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not from_number: missing.append("TWILIO_FROM or TWILIO_PHONE_NUMBER")
            return {"ok": False, "error": f"Twilio configuration missing: {', '.join(missing)}"}

        message_body = """Hi! Here's our menu:

https://www.kebabalab.com.au/menu.html

Take a look and give us a call back when you're ready to order!

Kebabalab
1/99 Carlisle St, St Kilda"""

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=_au_to_e164(from_number),
            to=_au_to_e164(to_phone)
        )

        logger.info(f"Menu link sent to customer: {_au_to_e164(to_phone)}")
        return {
            "ok": True,
            "messageSid": message.sid,
            "sentTo": _au_to_e164(to_phone),
            "message": "Menu link sent via SMS"
        }
    except Exception as e:
        import traceback
        logger.error(f"Error sending menu link: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_validate_menu_items(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if requested items exist in the menu. Returns list of invalid items if any."""
    try:
        logger.info(f"Validating menu items with params: {json.dumps(params, indent=2)}")
        menu = load_json_file("menu.json")
        items_to_check = params.get("items", [])
        synonyms = menu.get("synonyms", {})
        
        if not items_to_check:
            return {"ok": True, "allValid": True, "invalidItems": []}
        
        invalid_items = []
        valid_categories = set()
        valid_items = set()
        
        # Build valid items list from menu
        for category_name, category_items in menu.get("categories", {}).items():
            valid_categories.add(category_name.lower())
            for menu_item in category_items:
                item_name = menu_item.get("name", "").lower()
                valid_items.add(item_name)
                # Add variants if they exist
                if "variants" in menu_item:
                    for variant in menu_item["variants"]:
                        valid_items.add(f"{variant.lower()} {category_name.lower()}")
        
        # Add modifiers as valid
        for modifier_type in ["salads", "sauces", "extras"]:
            for modifier in menu.get("modifiers", {}).get(modifier_type, []):
                valid_items.add(modifier.get("name", "").lower())
        
        # Check each item
        for item in items_to_check:
            item_lower = str(item).lower().strip()
            
            # Check if marked as invalid in synonyms
            if synonyms.get(item_lower) == "INVALID_ITEM":
                invalid_items.append({
                    "requestedItem": item,
                    "reason": "Item not available on our menu"
                })
                continue
            
            # Apply synonym if exists
            if item_lower in synonyms:
                mapped_item = synonyms[item_lower].lower()
                # Check if the mapped item is valid
                if mapped_item in valid_items or any(mapped_item in vi for vi in valid_items):
                    continue  # Valid item found
                # Also check if it's a partial match
                for vi in valid_items:
                    if mapped_item in vi or vi in mapped_item:
                        break
                else:
                    invalid_items.append({
                        "requestedItem": item,
                        "reason": "Item not found on menu",
                        "mappedTo": mapped_item
                    })
            else:
                # Check if valid directly
                is_valid = (
                    item_lower in valid_items or
                    item_lower in valid_categories or
                    any(item_lower in valid_item for valid_item in valid_items)
                )
                
                if not is_valid:
                    invalid_items.append({
                        "requestedItem": item,
                        "reason": "Item not found on menu"
                    })
        
        result = {
            "ok": True,
            "allValid": len(invalid_items) == 0,
            "invalidItems": invalid_items,
            "message": f"Found {len(invalid_items)} invalid item(s)" if invalid_items else "All items valid"
        }
        logger.info(f"Menu validation result: {result}")
        return result
    except Exception as e:
        import traceback
        logger.error(f"Error validating menu items: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def tool_end_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """Signal to end the call"""
    logger.info("Ending call")
    return {"ok": True, "action": "end_call", "message": "Call ending"}

def tool_validate_item(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate if an item exists in the menu (optional tool)"""
    category = params.get("category")
    item_name = params.get("name")
    size = params.get("size")
    brand = params.get("brand")
    result = validate_menu_item(category, item_name, size, brand)
    logger.info(f"Item validation result: {result}")
    return result

def tool_notify_shop(params: Dict[str, Any]) -> Dict[str, Any]:
    """Send SMS to shop about new order (E.164, env fallback for FROM)."""
    try:
        logger.info(f"Notifying shop with params: {json.dumps(params, indent=2)}")
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token  = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM") or os.getenv("TWILIO_PHONE_NUMBER")
        to_number   = os.getenv("SHOP_ORDER_TO")

        if not all([account_sid, auth_token, from_number, to_number]):
            missing = []
            if not account_sid: missing.append("TWILIO_ACCOUNT_SID")
            if not auth_token: missing.append("TWILIO_AUTH_TOKEN")
            if not from_number: missing.append("TWILIO_FROM or TWILIO_PHONE_NUMBER")
            if not to_number: missing.append("SHOP_ORDER_TO")
            return {"ok": False, "error": f"Twilio not configured: {', '.join(missing)}"}

        order_id     = params.get("orderId")
        cart         = params.get("cart", [])
        totals       = params.get("totals", {})
        ready_at_iso = params.get("readyAtIso")
        contact      = params.get("contact", {})
        order_type   = params.get("order_type", "pickup")

        # Format pickup time
        ready_display = ready_at_iso
        try:
            tz = pytz.timezone(os.getenv("SHOP_TIMEZONE", "Australia/Melbourne"))
            ready_dt = datetime.fromisoformat(ready_at_iso.replace("Z", "+00:00"))
            if ready_dt.tzinfo is None:
                ready_dt = tz.localize(ready_dt)
            ready_display = ready_dt.strftime("%-I:%M %p")
        except Exception:
            pass

        # Summarise items (with salads/sauces)
        lines = []
        for idx, item in enumerate(cart, 1):
            qty = item.get("quantity", 1)
            parts = []
            if qty and qty > 1: parts.append(f"{qty}x")
            if item.get("size"):    parts.append(item["size"].capitalize())
            if item.get("protein"): parts.append(item["protein"].capitalize())
            if item.get("name"):    parts.append(item["name"])
            lines.append(f"{idx}. {' '.join(parts)}")
            if item.get("salads"): lines.append(f"   Salads: {', '.join(item['salads'])}")
            if item.get("sauces"): lines.append(f"   Sauces: {', '.join(item['sauces'])}")
            if item.get("extras"): lines.append(f"   Extras: {', '.join(item['extras'])}")

        body = (
            f"🧾 New order #{order_id}\n"
            f"Type: {order_type}\n"
            f"Ready: {ready_display}\n"
            f"Name: {contact.get('name', 'N/A')}\n"
            f"Phone: {contact.get('phone', 'N/A')}\n\n"
            "ORDER:\n" + ("\n".join(lines)) + "\n\n"
            f"TOTAL: ${totals.get('grand_total', 0):.2f}"
        )

        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=body,
            from_=_au_to_e164(from_number),
            to=_au_to_e164(to_number)
        )
        logger.info(f"Shop notification sent: {msg.sid}")
        return {"ok": True, "messageSid": msg.sid, "sentTo": _au_to_e164(to_number)}
    except Exception as e:
        logger.error(f"Error notifying shop: {str(e)}")
        return {"ok": False, "error": str(e)}

# NEW: Sauce validation tool
def tool_validate_sauce_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate sauce request and determine if it should be included or as a tub"""
    try:
        logger.info(f"Validating sauce request with params: {json.dumps(params, indent=2)}")
        sauce_request = params.get("sauceRequest", "").lower().strip()
        item_type = params.get("itemType", "").lower()
        
        # Default assumption: included unless explicitly stated otherwise
        result = {
            "ok": True,
            "included": True,
            "asTub": False,
            "sauce": sauce_request,
            "message": f"I'll include {sauce_request} sauce with your {item_type}."
        }
        
        # Check for explicit "on the side" or "separate" requests
        if any(phrase in sauce_request for phrase in ["on the side", "separate", "tub", "extra"]):
            result["included"] = False
            result["asTub"] = True
            result["message"] = f"I'll add a {sauce_request} sauce tub on the side."
        
        # Check for multiple sauces
        if " and " in sauce_request or " with " in sauce_request:
            sauces = [s.strip() for s in sauce_request.replace(" and ", ",").replace(" with ", ",").split(",")]
            if len(sauces) > 1:
                result["sauces"] = sauces
                result["message"] = f"I'll include {', '.join(sauces)} sauces with your {item_type}."
        
        logger.info(f"Sauce validation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error validating sauce request: {str(e)}")
        return {"ok": False, "error": str(e)}

# NEW: Test connection tool
def tool_test_connection(params: Dict[str, Any]) -> Dict[str, Any]:
    """Test server connection"""
    logger.info("Testing connection")
    return {"ok": True, "message": "Connection successful", "timestamp": datetime.now().isoformat()}

# NEW: Detect combos tool
def tool_detect_combos(params: Dict[str, Any]) -> Dict[str, Any]:
    """Detect and convert items to combos/meals"""
    try:
        logger.info(f"Detecting combos with params: {json.dumps(params, indent=2)}")
        cart = params.get("cart", [])
        if not cart or len(cart) < 2:
            return {"ok": True, "hasChanges": False, "updatedCart": cart}
        
        # Create a copy of the cart to modify
        updated_cart = cart.copy()
        has_changes = False
        
        # Define combo patterns
        combo_patterns = {
            "kebab_can": {
                "items": [
                    {"category": "kebabs", "any_size": True},
                    {"category": "drinks", "name": "Soft Drink Can (375ml)"}
                ],
                "combo_name": "Kebab & Can Combo",
                "price_adjustment": -1.0  # $1 discount
            },
            "hsp_can": {
                "items": [
                    {"category": "hsp", "any_size": True},
                    {"category": "drinks", "name": "Soft Drink Can (375ml)"}
                ],
                "combo_name": "HSP & Can Combo",
                "price_adjustment": -1.0  # $1 discount
            },
            "kebab_meal": {
                "items": [
                    {"category": "kebabs", "any_size": True},
                    {"category": "chips", "any_size": True},
                    {"category": "drinks", "name": "Soft Drink Can (375ml)"}
                ],
                "combo_name": "Kebab Meal",
                "price_adjustment": -2.0  # $2 discount
            },
            "hsp_meal": {
                "items": [
                    {"category": "hsp", "any_size": True},
                    {"category": "chips", "any_size": True},
                    {"category": "drinks", "name": "Soft Drink Can (375ml)"}
                ],
                "combo_name": "HSP Meal",
                "price_adjustment": -2.0  # $2 discount
            }
        }
        
        # Check for combos
        for combo_name, combo_config in combo_patterns.items():
            if check_combo_match(updated_cart, combo_config["items"]):
                # Convert to combo
                combo_items = []
                combo_size = None
                combo_protein = None
                
                # Find the main item (kebab or HSP)
                for item in updated_cart:
                    if item.get("category") in ["kebabs", "hsp"]:
                        combo_size = item.get("size")
                        combo_protein = item.get("protein")
                        break
                
                # Create combo item
                combo_item = {
                    "name": combo_config["combo_name"],
                    "category": "combos",
                    "size": combo_size,
                    "protein": combo_protein,
                    "quantity": 1,
                    "combo_items": combo_config["items"],
                    "price_adjustment": combo_config["price_adjustment"]
                }
                
                # Remove individual items from cart
                items_to_remove = []
                for item in updated_cart:
                    if item_matches_pattern(item, combo_config["items"]):
                        items_to_remove.append(item)
                
                for item in items_to_remove:
                    updated_cart.remove(item)
                
                # Add combo to cart
                updated_cart.append(combo_item)
                has_changes = True
                break  # Only apply one combo per call
        
        result = {
            "ok": True,
            "hasChanges": has_changes,
            "updatedCart": updated_cart
        }
        logger.info(f"Combo detection result: {result}")
        return result
        
    except Exception as e:
        import traceback
        logger.error(f"Error detecting combos: {str(e)}")
        traceback.print_exc()
        return {"ok": False, "error": str(e)}

def check_combo_match(cart: List[Dict], required_items: List[Dict]) -> bool:
    """Check if cart contains all required items for a combo"""
    cart_copy = cart.copy()
    
    for required_item in required_items:
        found = False
        for item in cart_copy:
            if item_matches_pattern(item, required_item):
                cart_copy.remove(item)
                found = True
                break
        if not found:
            return False
    
    return True

def item_matches_pattern(item: Dict, pattern: Dict) -> bool:
    """Check if an item matches a pattern"""
    if pattern.get("category") and item.get("category") != pattern.get("category"):
        return False
    
    if pattern.get("name") and item.get("name") != pattern.get("name"):
        return False
    
    # If pattern allows any size, don't check size
    if not pattern.get("any_size", False) and pattern.get("size"):
        if item.get("size") != pattern.get("size"):
            return False
    
    return True

# Tool mapping
TOOLS = {
    "checkOpen": tool_check_open,
    "getMenu": tool_get_menu,
    "getCallerInfo": tool_get_caller_info,
    "priceOrder": tool_price_order,
    "estimateReadyTime": tool_estimate_ready_time,
    "createOrder": tool_create_order,
    "sendReceipt": tool_send_receipt,
    "sendMenuLink": tool_send_menu_link,
    "validateMenuItems": tool_validate_menu_items,
    "validateItem": tool_validate_item,
    "endCall": tool_end_call,
    "notifyShop": tool_notify_shop,
    "validateSauceRequest": tool_validate_sauce_request,
    "testConnection": tool_test_connection,
    "detectCombos": tool_detect_combos,
}

# Webhook endpoints - handle both paths for compatibility
@app.post("/webhook")
async def vapi_webhook(request: Request):
    """Main webhook endpoint for VAPI"""
    try:
        data = await request.json()
        logger.info(f"Received VAPI webhook: {json.dumps(data, indent=2)}")
        
        # Set caller context if available
        if "call" in data and "phone" in data["call"]:
            caller_context.set(data["call"]["phone"])
        
        # Handle tool calls
        if "message" in data and "toolCalls" in data["message"]:
            tool_results = []
            for tool_call in data["message"]["toolCalls"]:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("parameters", {})
                
                # Handle case where parameters might be a string
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except:
                        tool_args = {}
                
                logger.info(f"Calling tool {tool_name} with args: {json.dumps(tool_args, indent=2)}")
                
                if tool_name in TOOLS:
                    result = TOOLS[tool_name](tool_args)
                    tool_results.append({
                        "toolCallId": tool_call.get("toolCallId"),
                        "result": result
                    })
                else:
                    tool_results.append({
                        "toolCallId": tool_call.get("toolCallId"),
                        "result": {"ok": False, "error": f"Unknown tool: {tool_name}"}
                    })
            
            return JSONResponse(content={"results": tool_results})
        
        # Handle other VAPI events as needed
        return JSONResponse(content={"status": "received"})
    
    except Exception as e:
        logger.error(f"VAPI webhook failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/vapi/webhook")
async def vapi_webhook_alt(request: Request):
    """Alternative webhook endpoint for VAPI compatibility"""
    return await vapi_webhook(request)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
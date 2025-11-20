"""
Comprehensive Test Suite for Stuffed Lamb Ordering System
Tests all menu items, pricing, modifiers, and business logic
"""

import sys
import os
import json
import copy
import pytest
from datetime import datetime
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure webhook auth is enabled during tests
os.environ.setdefault('WEBHOOK_SHARED_SECRET', 'test-secret')

from stuffed_lamb.server import (
    app, load_menu, init_database, tool_check_open, get_modifier_price
)
import stuffed_lamb.server as server_module


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Load menu before running any tests"""
    load_menu()
    init_database()
    server_module.WEBHOOK_SHARED_SECRET = os.environ.get('WEBHOOK_SHARED_SECRET')
    yield


@pytest.fixture
def webhook_headers():
    return {
        'Content-Type': 'application/json',
        'X-Stuffed-Lamb-Signature': os.environ.get('WEBHOOK_SHARED_SECRET', 'test-secret')
    }


class TestMenuLoading:
    """Test menu data loading and validation"""

    def test_menu_loads_successfully(self):
        """Menu file should load without errors"""
        assert load_menu() is True
        assert server_module.MENU is not None
        assert isinstance(server_module.MENU, dict)

    def test_menu_has_required_categories(self):
        """Menu should have all required categories"""
        categories = server_module.MENU.get('categories', {})
        assert 'mains' in categories
        assert 'drinks' in categories
        assert 'soups' in categories

    def test_menu_has_modifiers(self):
        """Menu should have modifiers section"""
        assert 'modifiers' in server_module.MENU
        modifiers = server_module.MENU['modifiers']
        assert 'extras' in modifiers


class TestMainDishes:
    """Test main dish pricing and configurations"""

    def test_jordanian_mansaf_base_price(self):
        """Jordanian Mansaf should have correct base price"""
        mains = server_module.MENU['categories']['mains']
        mansaf = next((item for item in mains if item['id'] == 'MANSAF'), None)
        assert mansaf is not None
        assert mansaf['price'] == 33.00
        assert 'Jordanian' in mansaf['name']

    def test_lamb_mandi_base_price(self):
        """Lamb Mandi should have correct base price"""
        mains = server_module.MENU['categories']['mains']
        lamb_mandi = next((item for item in mains if item['id'] == 'LAMB_MANDI'), None)
        assert lamb_mandi is not None
        assert lamb_mandi['price'] == 28.00

    def test_chicken_mandi_base_price(self):
        """Chicken Mandi should have correct base price"""
        mains = server_module.MENU['categories']['mains']
        chicken_mandi = next((item for item in mains if item['id'] == 'CHICKEN_MANDI'), None)
        assert chicken_mandi is not None
        assert chicken_mandi['price'] == 23.00

    def test_all_mains_have_descriptions(self):
        """All main dishes should have descriptions"""
        mains = server_module.MENU['categories']['mains']
        for item in mains:
            assert 'description' in item
            assert len(item['description']) > 0


class TestPricingCalculations:
    """Test pricing calculations with modifiers"""

    def test_lamb_mandi_with_nuts_addon(self):
        """Lamb Mandi + nuts addon = $28.00 + $2.00 = $30.00"""
        base_price = 28.00
        nuts_addon = 2.00
        expected_total = 30.00

        # From the menu, mandi_addons has nuts at $2.00
        addons = server_module.MENU['modifiers']['mandi_addons']
        nuts = next((a for a in addons if a['name'] == 'nuts'), None)
        assert nuts is not None
        assert nuts['price'] == nuts_addon

        total = base_price + nuts['price']
        assert total == expected_total

    def test_lamb_mandi_with_sultanas_addon(self):
        """Lamb Mandi + sultanas addon = $28.00 + $2.00 = $30.00"""
        base_price = 28.00
        sultanas_addon = 2.00
        expected_total = 30.00

        addons = server_module.MENU['modifiers']['mandi_addons']
        sultanas = next((a for a in addons if a['name'] == 'sultanas'), None)
        assert sultanas is not None
        assert sultanas['price'] == sultanas_addon

        total = base_price + sultanas['price']
        assert total == expected_total

    def test_lamb_mandi_with_both_addons(self):
        """Lamb Mandi + nuts + sultanas = $28.00 + $2.00 + $2.00 = $32.00"""
        base_price = 28.00
        expected_total = 32.00

        addons = server_module.MENU['modifiers']['mandi_addons']
        nuts = next((a for a in addons if a['name'] == 'nuts'), None)
        sultanas = next((a for a in addons if a['name'] == 'sultanas'), None)

        total = base_price + nuts['price'] + sultanas['price']
        assert total == expected_total

    def test_lamb_mandi_with_extras(self):
        """Test Lamb Mandi with various extras"""
        base_price = 28.00
        extras = server_module.MENU['modifiers']['extras']

        # Extra green chilli (+$1.00)
        green_chilli = next((e for e in extras if e['name'] == 'green chilli'), None)
        assert green_chilli['price'] == 1.00

        # Extra potato (+$1.00)
        potato = next((e for e in extras if e['name'] == 'potato'), None)
        assert potato['price'] == 1.00

        # Extra tzatziki (+$1.00)
        tzatziki = next((e for e in extras if e['name'] == 'tzatziki'), None)
        assert tzatziki['price'] == 1.00

        # Extra rice on plate (+$5.00)
        extra_rice = next((e for e in extras if e['name'] == 'extra rice on plate'), None)
        assert extra_rice['price'] == 5.00

        # Total with all extras
        total_with_all_extras = (
            base_price +
            green_chilli['price'] +
            potato['price'] +
            tzatziki['price'] +
            extra_rice['price']
        )
        assert total_with_all_extras == 36.00

    def test_chicken_mandi_full_customization(self):
        """Test Chicken Mandi with all addons and extras"""
        base_price = 23.00

        # Addons
        addons = server_module.MENU['modifiers']['mandi_addons']
        nuts = next((a for a in addons if a['name'] == 'nuts'), None)
        sultanas = next((a for a in addons if a['name'] == 'sultanas'), None)

        # Extras
        extras = server_module.MENU['modifiers']['extras']
        green_chilli = next((e for e in extras if e['name'] == 'green chilli'), None)
        potato = next((e for e in extras if e['name'] == 'potato'), None)
        tzatziki = next((e for e in extras if e['name'] == 'tzatziki'), None)
        chilli_sauce = next((e for e in extras if e['name'] == 'chilli mandi sauce'), None)
        extra_rice = next((e for e in extras if e['name'] == 'extra rice on plate'), None)

        # Calculate total
        total = (
            base_price +
            nuts['price'] +           # $2.00
            sultanas['price'] +        # $2.00
            green_chilli['price'] +    # $1.00
            potato['price'] +          # $1.00
            tzatziki['price'] +        # $1.00
            chilli_sauce['price'] +    # $1.00
            extra_rice['price']        # $5.00
        )

        # Expected: $23.00 + $2.00 + $2.00 + $1.00 + $1.00 + $1.00 + $1.00 + $5.00 = $36.00
        assert total == 36.00

    def test_mansaf_with_extras(self):
        """Test Mansaf with extra jameed and rice"""
        base_price = 33.00
        extras = server_module.MENU['modifiers']['extras']

        # Extra jameed (+$8.40)
        extra_jameed = next((e for e in extras if e['name'] == 'extra jameed'), None)
        assert extra_jameed is not None
        assert extra_jameed['price'] == 8.40
        assert 'MANSAF' in extra_jameed['applies_to']

        # Extra rice mansaf (+$8.40)
        extra_rice = next((e for e in extras if e['name'] == 'extra rice mansaf'), None)
        assert extra_rice is not None
        assert extra_rice['price'] == 8.40
        assert 'MANSAF' in extra_rice['applies_to']

        # Total with both extras
        total = base_price + extra_jameed['price'] + extra_rice['price']
        assert total == 49.80  # $33.00 + $8.40 + $8.40


class TestPricingHelpers:
    def test_modifier_helper_tracks_menu(self, monkeypatch):
        extras_copy = copy.deepcopy(server_module.MENU['modifiers']['extras'])
        mutated = copy.deepcopy(extras_copy)
        for entry in mutated:
            if entry['name'] == 'tzatziki':
                entry['price'] = 1.75
        monkeypatch.setitem(server_module.MENU['modifiers'], 'extras', mutated)
        assert get_modifier_price('tzatziki', 'extras') == pytest.approx(1.75)
        monkeypatch.setitem(server_module.MENU['modifiers'], 'extras', extras_copy)


class TestNlpExtras:
    """NLP should recognize extras even when callers omit the word 'extra'."""

    def test_extra_rice_detected_without_trigger_word(self):
        call_id = 'extra-rice-call'
        phone = '+61123456789'
        description = "lamb mandi rice on top"

        with app.test_request_context(json={
            "message": {
                "call": {
                    "id": call_id,
                    "customer": {"number": phone}
                }
            }
        }):
            server_module.session_clear(phone)
            result = server_module.tool_quick_add_item({"description": description})

        assert result['ok'] is True
        item = result['item']
        assert 'extra rice on plate' in item.get('extras', [])
        assert item['price'] == pytest.approx(33.00)
        server_module.session_clear(phone)


class TestDrinksAndSides:
    """Test drinks and side items"""

    def test_soft_drink_pricing(self):
        """Soft drinks should be $3.00"""
        drinks = server_module.MENU['categories']['drinks']
        soft_drink = next((d for d in drinks if d['id'] == 'SOFT_DRINK'), None)
        assert soft_drink is not None
        assert soft_drink['price'] == 3.00
        assert 'brands' in soft_drink
        assert 'Coke' in soft_drink['brands']
        assert 'Sprite' in soft_drink['brands']

    def test_water_pricing(self):
        """Bottled water should be $2.00"""
        drinks = server_module.MENU['categories']['drinks']
        water = next((d for d in drinks if d['id'] == 'WATER'), None)
        assert water is not None
        assert water['price'] == 2.00

    def test_soup_of_the_day_pricing(self):
        """Soup of the day should be $7.00"""
        soups = server_module.MENU['categories']['soups']
        soup = next((s for s in soups if s['id'] == 'SOUP_DAY'), None)
        assert soup is not None
        assert soup['price'] == 7.00


class TestExtrasAndModifiers:
    """Test individual extras pricing"""

    def test_basic_extras_one_dollar(self):
        """Test all $1.00 extras"""
        extras = server_module.MENU['modifiers']['extras']
        one_dollar_extras = ['nuts', 'sultanas', 'tzatziki', 'chilli mandi sauce',
                            'bread', 'green chilli', 'potato']

        for extra_name in one_dollar_extras:
            extra = next((e for e in extras if e['name'] == extra_name), None)
            assert extra is not None, f"Extra '{extra_name}' not found"
            assert extra['price'] == 1.00, f"Extra '{extra_name}' should be $1.00"

    def test_rice_side_portion(self):
        """Rice side portion should be $7.00"""
        extras = server_module.MENU['modifiers']['extras']
        rice = next((e for e in extras if e['name'] == 'rice'), None)
        assert rice is not None
        assert rice['price'] == 7.00

    def test_extra_rice_on_plate(self):
        """Extra rice on plate should be $5.00"""
        extras = server_module.MENU['modifiers']['extras']
        extra_rice = next((e for e in extras if e['name'] == 'extra rice on plate'), None)
        assert extra_rice is not None
        assert extra_rice['price'] == 5.00


class TestComplexOrders:
    """Test complex multi-item orders"""

    def test_family_order(self):
        """Test a typical family order"""
        # 1x Mansaf ($33.00)
        # 1x Lamb Mandi with nuts ($28.00 + $2.00)
        # 1x Chicken Mandi ($23.00)
        # 3x Soft Drinks ($3.00 each)
        # 1x Soup of the Day ($7.00)

        mains = server_module.MENU['categories']['mains']
        drinks = server_module.MENU['categories']['drinks']
        soups = server_module.MENU['categories']['soups']
        addons = server_module.MENU['modifiers']['mandi_addons']

        mansaf = next(item for item in mains if item['id'] == 'MANSAF')
        lamb_mandi = next(item for item in mains if item['id'] == 'LAMB_MANDI')
        chicken_mandi = next(item for item in mains if item['id'] == 'CHICKEN_MANDI')
        soft_drink = next(d for d in drinks if d['id'] == 'SOFT_DRINK')
        soup = next(s for s in soups if s['id'] == 'SOUP_DAY')
        nuts = next(a for a in addons if a['name'] == 'nuts')

        total = (
            mansaf['price'] +                    # $33.00
            (lamb_mandi['price'] + nuts['price']) +  # $30.00
            chicken_mandi['price'] +             # $23.00
            (soft_drink['price'] * 3) +          # $9.00
            soup['price']                        # $7.00
        )

        assert total == 102.00

    def test_order_from_user_example(self):
        """Test the example order from user message"""
        # User showed: Lamb Mandi with Add Nuts ($2.00) + Add Sultanas ($2.00)
        # Plus extras but let's test the base from website display

        mains = server_module.MENU['categories']['mains']
        addons = server_module.MENU['modifiers']['mandi_addons']

        lamb_mandi = next(item for item in mains if item['id'] == 'LAMB_MANDI')
        nuts = next(a for a in addons if a['name'] == 'nuts')
        sultanas = next(a for a in addons if a['name'] == 'sultanas')

        # Base + addons
        subtotal = lamb_mandi['price'] + nuts['price'] + sultanas['price']
        assert subtotal == 32.00  # $28.00 + $2.00 + $2.00


class TestSynonyms:
    """Test menu synonym handling"""

    def test_synonym_mappings_exist(self):
        """Menu should have synonym mappings"""
        assert 'synonyms' in server_module.MENU
        synonyms = server_module.MENU['synonyms']
        assert isinstance(synonyms, dict)

    def test_common_synonyms(self):
        """Test common synonym mappings"""
        synonyms = server_module.MENU['synonyms']
        assert 'lamb' in synonyms
        assert 'chicken' in synonyms
        assert 'coke' in synonyms
        assert 'soup' in synonyms


class TestBusinessHours:
    """Test business hours configuration"""

    def test_hours_file_exists(self):
        """Hours configuration should be loadable"""
        hours_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'hours.json'
        )
        assert os.path.exists(hours_file)

        with open(hours_file, 'r') as f:
            hours = json.load(f)

        assert 'monday' in hours
        assert 'sunday' in hours

    def test_closed_days(self):
        """Monday and Tuesday should be closed"""
        hours_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'hours.json'
        )

        with open(hours_file, 'r') as f:
            hours = json.load(f)

        assert hours['monday'] == 'closed'
        assert hours['tuesday'] == 'closed'


class TestCheckOpenTool:
    def test_closed_day_message(self, monkeypatch):
        closed_day = server_module.SHOP_TIMEZONE.localize(datetime(2024, 1, 1, 12, 0))
        monkeypatch.setattr(server_module, 'get_current_time', lambda: closed_day)
        result = tool_check_open({})
        assert result['isOpen'] is False
        assert 'closed' in result['message'].lower()

    def test_open_weekend_hours(self, monkeypatch):
        open_day = server_module.SHOP_TIMEZONE.localize(datetime(2024, 1, 6, 14, 0))
        monkeypatch.setattr(server_module, 'get_current_time', lambda: open_day)
        result = tool_check_open({})
        assert result['isOpen'] is True
        assert result['openTime'] == '13:00'
        assert result['closeTime'] == '22:00'


class TestBusinessConfiguration:
    """Test business configuration"""

    def test_business_details(self):
        """Business details should be correct"""
        business_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data',
            'business.json'
        )

        with open(business_file, 'r') as f:
            business = json.load(f)

        details = business['business_details']
        assert details['name'] == 'Stuffed Lamb'
        assert 'Reservoir' in details['address']
        assert details['timezone'] == 'Australia/Melbourne'
        assert details['cuisine'] == 'Middle Eastern'


class TestGSTCalculations:
    """Test GST/Tax calculations"""

    def test_gst_on_lamb_mandi(self):
        """Calculate GST on Lamb Mandi"""
        price = 28.00
        gst_rate = 0.10

        # Prices are GST-inclusive
        # GST = price × (gst_rate / (1 + gst_rate))
        gst_component = price * (gst_rate / (1 + gst_rate))

        # Should be approximately $2.55
        assert abs(gst_component - 2.55) < 0.01

    def test_gst_on_total_order(self):
        """Calculate GST on a complete order"""
        # Mansaf ($33.00) + Chicken Mandi ($23.00) = $56.00
        total = 56.00
        gst_rate = 0.10

        gst_component = total * (gst_rate / (1 + gst_rate))

        # Should be approximately $5.09
        assert abs(gst_component - 5.09) < 0.01


class TestWebhookSecurity:
    def test_missing_signature_rejected(self):
        client = app.test_client()
        payload = {
            "message": {
                "type": "tool",
                "toolCalls": []
            }
        }
        response = client.post('/webhook', json=payload)
        assert response.status_code == 401


class TestWebhookFlow:
    def _build_payload(self, function_name: str, arguments: Dict, call_id: str, phone: str) -> Dict:
        return {
            "message": {
                "type": "tool",
                "call": {
                    "id": call_id,
                    "customer": {"number": phone}
                },
                "toolCalls": [
                    {
                        "id": f"{function_name}-call",
                        "function": {
                            "name": function_name,
                            "arguments": arguments
                        }
                    }
                ]
            }
        }

    def test_full_order_flow_via_webhook(self, webhook_headers):
        client = app.test_client()
        call_id = 'pytest-call'
        phone = '+61411111111'

        # Quick add
        payload = self._build_payload('quickAddItem', {"description": "lamb mandi with nuts and sultanas"}, call_id, phone)
        resp = client.post('/webhook', json=payload, headers=webhook_headers)
        assert resp.status_code == 200
        result = resp.get_json()['results'][0]['result']
        assert result['ok'] is True

        # Price cart
        payload = self._build_payload('priceCart', {}, call_id, phone)
        resp = client.post('/webhook', json=payload, headers=webhook_headers)
        assert resp.status_code == 200
        assert resp.get_json()['results'][0]['result']['ok'] is True

        # Set pickup time
        payload = self._build_payload('setPickupTime', {"requestedTime": "in 30 minutes"}, call_id, phone)
        resp = client.post('/webhook', json=payload, headers=webhook_headers)
        assert resp.get_json()['results'][0]['result']['ok'] is True

        with server_module.DatabaseConnection() as cursor:
            cursor.execute('SELECT COUNT(*) FROM orders')
            before_count = cursor.fetchone()[0]

        # Create order
        create_args = {
            "customerName": "Test Caller",
            "customerPhone": phone,
            "sendSMS": False
        }
        payload = self._build_payload('createOrder', create_args, call_id, phone)
        resp = client.post('/webhook', json=payload, headers=webhook_headers)
        result = resp.get_json()['results'][0]['result']
        assert result['ok'] is True
        assert result['orderNumber']

        with server_module.DatabaseConnection() as cursor:
            cursor.execute('SELECT COUNT(*) FROM orders')
            after_count = cursor.fetchone()[0]
        assert after_count == before_count + 1

        # Clean up session for other tests
        server_module.session_clear(phone)


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v', '--tb=short'])

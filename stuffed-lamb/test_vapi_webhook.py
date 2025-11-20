#!/usr/bin/env python3
"""
VAPI Webhook Testing Suite for Stuffed Lamb
Simulates VAPI voice ordering calls to test the system end-to-end
"""

import requests
import json
import hmac
import hashlib
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime
import os

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class VAPIWebhookTester:
    def __init__(self, webhook_url: str, secret: str = None):
        self.url = webhook_url
        self.secret = secret or os.getenv('WEBHOOK_SHARED_SECRET', 'test-secret-key')
        self.test_results = []
        self.phone_number = "+61412345678"
        self.session_id = "test-session-001"

    def create_signature(self, payload: Dict[str, Any]) -> str:
        """Return the shared secret (server does simple string comparison)"""
        # Note: The server expects the raw secret in the header, not an HMAC hash
        # This is a simple authentication method, not cryptographic signature verification
        return self.secret

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate a VAPI webhook call for a specific tool"""

        payload = {
            "message": {
                "type": "tool-calls",
                "toolCalls": [
                    {
                        "id": f"call_{int(time.time())}",
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(params)
                        }
                    }
                ],
                "call": {
                    "customer": {
                        "number": self.phone_number
                    }
                }
            }
        }

        signature = self.create_signature(payload)

        try:
            response = requests.post(
                self.url,
                json=payload,
                headers={
                    'X-Stuffed-Lamb-Signature': signature,
                    'Content-Type': 'application/json'
                },
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                # Handle VAPI response format with results array
                if 'results' in result and len(result['results']) > 0:
                    # Extract the actual result from the VAPI response format
                    return result['results'][0].get('result', result['results'][0])
                return result
            else:
                return {
                    "ok": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except requests.exceptions.ConnectionError:
            return {
                "ok": False,
                "error": "Connection refused - is the server running?"
            }
        except Exception as e:
            return {
                "ok": False,
                "error": f"Exception: {str(e)}"
            }

    def log_test(self, category: str, test_name: str, input_data: str,
                 result: Dict[str, Any], expected: str = None):
        """Log test result"""
        success = result.get('ok', False)

        self.test_results.append({
            'category': category,
            'test': test_name,
            'input': input_data,
            'expected': expected,
            'result': result,
            'success': success
        })

        status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if success else f"{Colors.RED}❌ FAIL{Colors.RESET}"
        print(f"\n{status} {Colors.BOLD}{test_name}{Colors.RESET}")
        print(f"  Input: {Colors.BLUE}{input_data}{Colors.RESET}")

        if success:
            print(f"  Result: {result.get('message', 'Success')}")
        else:
            print(f"  Error: {Colors.RED}{result.get('error', 'Unknown error')}{Colors.RESET}")

        if expected:
            print(f"  Expected: {expected}")

    def test_basic_items(self):
        """Test basic menu item ordering"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 1: BASIC MENU ITEMS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        tests = [
            ("lamb mandi", "Should add Lamb Mandi ($28)"),
            ("chicken mandi", "Should add Chicken Mandi ($23)"),
            ("mansaf", "Should add Jordanian Mansaf ($33)"),
            ("soup of the day", "Should add Soup ($7)"),
            ("soft drink", "Should add Soft Drink ($3)"),
            ("bottle of water", "Should add Water ($2)"),
            ("coke", "Should add Soft Drink - Coke"),
            ("sprite", "Should add Soft Drink - Sprite"),
        ]

        for description, expected in tests:
            result = self.call_tool("quickAddItem", {"description": description})
            self.log_test("Basic Items", description, description, result, expected)
            time.sleep(0.1)

    def test_quantities(self):
        """Test quantity parsing"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 2: QUANTITY PARSING{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        tests = [
            ("2 lamb mandis", "Should add 2x Lamb Mandi"),
            ("three chicken mandi", "Should add 3x Chicken Mandi"),
            ("5 cokes", "Should add 5x Soft Drink"),
            ("one mansaf", "Should add 1x Mansaf"),
        ]

        for description, expected in tests:
            result = self.call_tool("quickAddItem", {"description": description})
            self.log_test("Quantities", description, description, result, expected)
            time.sleep(0.1)

    def test_addons_and_extras(self):
        """Test add-ons and extras detection"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 3: ADD-ONS & EXTRAS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        tests = [
            ("lamb mandi with nuts", "Should add nuts addon (+$2)"),
            ("lamb mandi with sultanas", "Should add sultanas addon (+$2)"),
            ("lamb mandi with nuts and sultanas", "Should add both addons (+$4)"),
            ("chicken mandi add nuts", "Should add nuts to chicken"),
            ("mansaf with extra jameed", "Should add extra jameed (+$8.40)"),
            ("lamb mandi with extra rice on plate", "Should add extra rice (+$5)"),
            ("chicken with extra tzatziki", "Should add extra tzatziki (+$1)"),
        ]

        for description, expected in tests:
            result = self.call_tool("quickAddItem", {"description": description})
            self.log_test("Add-ons & Extras", description, description, result, expected)
            time.sleep(0.1)

    def test_pronunciation_variants(self):
        """Test accent and pronunciation variants"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 4: ACCENT & PRONUNCIATION VARIANTS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        tests = [
            # From pronunciations.json
            ("man saff", "Australian accent - Mansaf"),
            ("mun saf", "Alternative mansaf"),
            ("lam mandi", "Dropped 'b' - lamb"),
            ("lamb mondi", "Alternative spelling"),
            ("lamb mandy", "Alternative spelling"),
            ("chikin mandi", "Typo - chicken"),
            ("chook mandi", "Aussie slang - chicken"),
            ("chicken mondy", "Alternative spelling"),

            # Modifiers
            ("nutz", "Typo - nuts"),
            ("raisins", "Synonym - sultanas"),
            ("raisens", "Typo - raisins/sultanas"),
            ("garlic yogurt", "Synonym - tzatziki"),
            ("tzaziki", "Typo - tzatziki"),

            # From synonyms
            ("mensaf", "Alternative spelling"),
            ("mansaaf", "Alternative spelling"),
            ("mansaff", "Alternative spelling"),
            ("chook", "Aussie - chicken mandi"),
            ("just lamb", "Casual - lamb mandi"),
        ]

        for variant, description in tests:
            result = self.call_tool("quickAddItem", {"description": variant})
            self.log_test("Pronunciations", description, variant, result)
            time.sleep(0.1)

    def test_complex_orders(self):
        """Test complex multi-item orders"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 5: COMPLEX ORDERS{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        # Clear cart first
        self.call_tool("clearCart", {})

        steps = [
            ("lamb mandi with nuts and sultanas", "Add lamb with both addons"),
            ("2 chicken mandis", "Add 2 chickens"),
            ("mansaf with extra jameed", "Add mansaf with extra"),
            ("3 cokes and 2 waters", "Add drinks"),
        ]

        for description, expected in steps:
            result = self.call_tool("quickAddItem", {"description": description})
            self.log_test("Complex Order", expected, description, result)
            time.sleep(0.1)

        # Check cart state
        cart_result = self.call_tool("getCartState", {})
        self.log_test("Complex Order", "Get cart state", "getCartState", cart_result, "Should have 4-5 items")

        # Price cart
        price_result = self.call_tool("priceCart", {})
        self.log_test("Complex Order", "Price cart", "priceCart", price_result, "Should calculate total with GST")

    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 6: EDGE CASES & ERROR HANDLING{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        tests = [
            ("burger", "Should gracefully fail - not on menu"),
            ("pizza", "Should gracefully fail - not on menu"),
            ("", "Should fail - empty description"),
            ("the thing with yogurt", "Vague - might fail or match mansaf"),
            ("lamb", "Should match lamb mandi via synonym"),
            ("chicken", "Should match chicken mandi via synonym"),
            ("gimme a lamb", "Casual speech"),
            ("can I get the chicken please", "Polite phrasing"),
        ]

        for description, expected in tests:
            result = self.call_tool("quickAddItem", {"description": description})
            self.log_test("Edge Cases", expected, description, result)
            time.sleep(0.1)

    def test_full_order_flow(self):
        """Test complete order flow from start to finish"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 7: FULL ORDER FLOW{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        # 1. Clear cart
        result = self.call_tool("clearCart", {})
        self.log_test("Full Flow", "Clear cart", "clearCart", result)

        # 2. Check if open
        result = self.call_tool("checkOpen", {})
        self.log_test("Full Flow", "Check if open", "checkOpen", result)

        # 3. Get caller context
        result = self.call_tool("getCallerSmartContext", {"phoneNumber": self.phone_number})
        self.log_test("Full Flow", "Get caller context", "getCallerSmartContext", result)

        # 4. Add items
        result = self.call_tool("quickAddItem", {"description": "lamb mandi with nuts"})
        self.log_test("Full Flow", "Add lamb mandi", "lamb mandi with nuts", result)

        result = self.call_tool("quickAddItem", {"description": "coke"})
        self.log_test("Full Flow", "Add coke", "coke", result)

        # 5. Get cart state
        result = self.call_tool("getCartState", {})
        self.log_test("Full Flow", "Review cart", "getCartState", result)

        # 6. Price cart
        result = self.call_tool("priceCart", {})
        self.log_test("Full Flow", "Price cart", "priceCart", result)

        # 7. Get order summary
        result = self.call_tool("getOrderSummary", {})
        self.log_test("Full Flow", "Get order summary", "getOrderSummary", result)

        # 8. Estimate ready time
        result = self.call_tool("estimateReadyTime", {})
        self.log_test("Full Flow", "Estimate ready time", "estimateReadyTime", result)

        # 9. Create order (with sendSMS = false for testing)
        result = self.call_tool("createOrder", {
            "customerName": "Test Customer",
            "customerPhone": self.phone_number,
            "notes": "This is a test order",
            "sendSMS": False
        })
        self.log_test("Full Flow", "Create order", "createOrder", result)

    def test_missing_pronunciation_variants(self):
        """Test variants that SHOULD work but might not (from our research)"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}CATEGORY 8: MISSING PRONUNCIATION VARIANTS (Expected to Fail){Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}")

        tests = [
            # Australian accents
            ("mahn-sahf", "Australian accent - mansaf"),
            ("lammondy", "Australian accent - lamb mandi"),
            ("lam", "Short form - lamb mandi"),

            # Middle Eastern accents
            ("man-saaf", "Middle Eastern - mansaf"),
            ("jah-meed", "Phonetic - jameed"),
            ("jah-meet", "Alternative - jameed"),

            # Fast speech
            ("lmandi", "Fast speech - lamb mandi"),
            ("msaf", "Fast speech - mansaf"),
            ("gimme chook", "Fast casual - chicken mandi"),

            # Common errors
            ("man sack", "Mishear - mansaf"),
            ("man staff", "Mishear - mansaf"),
            ("chicken monday", "Mishear - chicken mandi"),

            # Descriptive
            ("the lamb with yogurt", "Descriptive - mansaf"),
            ("lamb on rice", "Descriptive - lamb mandi"),
            ("half chicken", "Descriptive - chicken mandi"),
        ]

        for variant, description in tests:
            result = self.call_tool("quickAddItem", {"description": variant})
            self.log_test("Missing Variants", description, variant, result)
            time.sleep(0.1)

    def print_summary(self):
        """Print test summary report"""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.BOLD}TEST SUMMARY REPORT{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*70}{Colors.RESET}\n")

        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0

        print(f"{Colors.BOLD}Overall Results:{Colors.RESET}")
        print(f"  Total Tests: {total}")
        print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"  {Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.RESET}")

        # Group by category
        categories = {}
        for result in self.test_results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if result['success']:
                categories[cat]['passed'] += 1

        print(f"\n{Colors.BOLD}Results by Category:{Colors.RESET}")
        for cat, stats in categories.items():
            rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            status = f"{Colors.GREEN}✅{Colors.RESET}" if rate >= 90 else f"{Colors.YELLOW}⚠️{Colors.RESET}" if rate >= 70 else f"{Colors.RED}❌{Colors.RESET}"
            print(f"  {status} {cat}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")

        # Show failures
        failures = [r for r in self.test_results if not r['success']]
        if failures:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed Tests:{Colors.RESET}")
            for i, fail in enumerate(failures[:10], 1):  # Show first 10
                print(f"\n  {i}. {fail['test']}")
                print(f"     Input: {fail['input']}")
                print(f"     Error: {fail['result'].get('error', 'Unknown')}")

            if len(failures) > 10:
                print(f"\n  ... and {len(failures) - 10} more failures")

        # Production readiness
        print(f"\n{Colors.BOLD}Production Readiness Assessment:{Colors.RESET}")
        if success_rate >= 95:
            print(f"  {Colors.GREEN}✅ EXCELLENT - Ready for production{Colors.RESET}")
        elif success_rate >= 85:
            print(f"  {Colors.YELLOW}⚠️  GOOD - Minor improvements needed{Colors.RESET}")
        elif success_rate >= 70:
            print(f"  {Colors.YELLOW}⚠️  FAIR - Significant improvements needed{Colors.RESET}")
        else:
            print(f"  {Colors.RED}❌ POOR - Major fixes required before production{Colors.RESET}")

    def save_report(self, filename: str = "test_results.json"):
        """Save detailed test results to file"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.test_results),
            'passed': sum(1 for r in self.test_results if r['success']),
            'failed': sum(1 for r in self.test_results if not r['success']),
            'success_rate': (sum(1 for r in self.test_results if r['success']) / len(self.test_results) * 100) if self.test_results else 0,
            'results': self.test_results
        }

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{Colors.GREEN}📄 Detailed report saved to: {filename}{Colors.RESET}")

def main():
    """Main test runner"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                                                                    ║")
    print("║          STUFFED LAMB - VAPI WEBHOOK TESTING SUITE                ║")
    print("║                                                                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")

    # Configuration
    webhook_url = os.getenv('WEBHOOK_URL', 'http://localhost:8000/webhook')
    secret = os.getenv('WEBHOOK_SHARED_SECRET', 'test-secret-key')

    print(f"Testing webhook: {Colors.BLUE}{webhook_url}{Colors.RESET}")
    print(f"Using secret: {Colors.BLUE}{'*' * 20}{Colors.RESET}\n")

    tester = VAPIWebhookTester(webhook_url, secret)

    # Run all test categories
    try:
        tester.test_basic_items()
        tester.test_quantities()
        tester.test_addons_and_extras()
        tester.test_pronunciation_variants()
        tester.test_complex_orders()
        tester.test_edge_cases()
        tester.test_full_order_flow()
        tester.test_missing_pronunciation_variants()

        # Print summary
        tester.print_summary()

        # Save report
        tester.save_report('/home/user/Claude/stuffed-lamb/test_results.json')

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Testing interrupted by user{Colors.RESET}")
        tester.print_summary()
    except Exception as e:
        print(f"\n\n{Colors.RED}Error during testing: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

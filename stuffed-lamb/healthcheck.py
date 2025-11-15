#!/usr/bin/env python3
"""
Stuffed Lamb Health Check Script
==================================

Verifies the system is running correctly.
Usage: python healthcheck.py [--url http://localhost:8000]
"""

import sys
import argparse
import json
try:
    import urllib.request
    import urllib.error
except ImportError:
    print("ERROR: urllib not available")
    sys.exit(1)

def check_health(base_url: str) -> bool:
    """Check if the server is healthy"""
    url = f"{base_url}/health"

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get('status') == 'healthy':
                    print(f"✓ Health check PASSED: {url}")
                    return True
                else:
                    print(f"✗ Health check FAILED: unexpected response: {data}")
                    return False
            else:
                print(f"✗ Health check FAILED: HTTP {response.status}")
                return False
    except urllib.error.URLError as e:
        print(f"✗ Health check FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ Health check FAILED: {e}")
        return False

def check_endpoints(base_url: str) -> bool:
    """Check if critical endpoints are accessible"""
    endpoints = [
        "/health",
        "/vapi/webhook",
    ]

    all_ok = True
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            # For webhook, we just check it's accessible (POST endpoints)
            if endpoint == "/vapi/webhook":
                # Try a simple GET to see if endpoint exists
                req = urllib.request.Request(url, method='POST')
                req.add_header('Content-Type', 'application/json')
                with urllib.request.urlopen(req, data=b'{}', timeout=5) as response:
                    # We expect some response, even if it's an error
                    print(f"✓ Endpoint accessible: {endpoint}")
            else:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        print(f"✓ Endpoint accessible: {endpoint}")
                    else:
                        print(f"✗ Endpoint returned HTTP {response.status}: {endpoint}")
                        all_ok = False
        except urllib.error.HTTPError as e:
            # For POST endpoints, we might get 400 which is ok (means endpoint exists)
            if endpoint == "/vapi/webhook" and e.code == 400:
                print(f"✓ Endpoint accessible: {endpoint} (returns 400 for invalid request)")
            else:
                print(f"✗ Endpoint error HTTP {e.code}: {endpoint}")
                all_ok = False
        except Exception as e:
            print(f"✗ Endpoint failed: {endpoint} - {e}")
            all_ok = False

    return all_ok

def main():
    parser = argparse.ArgumentParser(description="Stuffed Lamb Health Check")
    parser.add_argument('--url', default='http://localhost:8000',
                       help='Base URL of the server (default: http://localhost:8000)')
    parser.add_argument('--full', action='store_true',
                       help='Run full endpoint checks')
    args = parser.parse_args()

    print(f"Checking Stuffed Lamb server at {args.url}...")
    print()

    # Basic health check
    health_ok = check_health(args.url)

    # Full endpoint check if requested
    if args.full:
        print()
        print("Running full endpoint checks...")
        endpoints_ok = check_endpoints(args.url)
    else:
        endpoints_ok = True

    print()
    if health_ok and endpoints_ok:
        print("✓ All checks PASSED")
        sys.exit(0)
    else:
        print("✗ Some checks FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()

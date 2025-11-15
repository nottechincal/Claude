#!/usr/bin/env python3
"""
Stuffed Lamb Server - Simple Startup Script
============================================

This script starts the Stuffed Lamb VAPI ordering server.

Usage:
    python run.py                    # Run on default port 8000
    python run.py --port 5000        # Run on custom port
    python run.py --help            # Show help
"""

import sys
import argparse
from stuffed_lamb.server import main, init_database, load_menu, logger

def check_environment():
    """Check if .env file exists and warn if not configured"""
    import os
    from pathlib import Path

    env_file = Path('.env')
    env_example = Path('.env.example')

    if not env_file.exists():
        logger.warning("=" * 60)
        logger.warning("⚠️  WARNING: .env file not found!")
        logger.warning("=" * 60)
        logger.warning("1. Copy .env.example to .env:")
        logger.warning("   cp .env.example .env")
        logger.warning("")
        logger.warning("2. Edit .env with your actual credentials:")
        logger.warning("   - TWILIO_ACCOUNT_SID")
        logger.warning("   - TWILIO_AUTH_TOKEN")
        logger.warning("   - TWILIO_FROM (your Twilio phone number)")
        logger.warning("   - SHOP_ORDER_TO (shop phone for notifications)")
        logger.warning("=" * 60)
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            logger.info("Exiting. Please configure .env first.")
            sys.exit(1)
    else:
        # Check for placeholder values
        with open(env_file, 'r') as f:
            content = f.read()

        warnings = []
        if 'your_twilio_account_sid_here' in content:
            warnings.append("TWILIO_ACCOUNT_SID needs to be configured")
        if 'your_twilio_auth_token_here' in content:
            warnings.append("TWILIO_AUTH_TOKEN needs to be configured")
        if '+61xxxxxxxxxx' in content:
            warnings.append("Phone numbers need to be configured (TWILIO_FROM, SHOP_ORDER_TO)")

        if warnings:
            logger.warning("=" * 60)
            logger.warning("⚠️  WARNING: Placeholder values found in .env!")
            logger.warning("=" * 60)
            for warning in warnings:
                logger.warning(f"   • {warning}")
            logger.warning("=" * 60)
            logger.warning("SMS notifications will NOT work until configured.")
            logger.warning("See ENV_SETUP_GUIDE.md for detailed instructions.")
            logger.warning("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Stuffed Lamb VAPI Ordering Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Run on port 8000 (default)
  python run.py --port 5000        # Run on port 5000
  python run.py --skip-checks      # Skip environment checks

For more information, see README.md
        """
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to run the server on (default: from .env PORT or 8000)'
    )
    parser.add_argument(
        '--skip-checks',
        action='store_true',
        help='Skip environment configuration checks'
    )

    args = parser.parse_args()

    # Set port if specified
    if args.port:
        import os
        os.environ['PORT'] = str(args.port)

    # Check environment unless skipped
    if not args.skip_checks:
        check_environment()

    # Run the server
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}", exc_info=True)
        sys.exit(1)

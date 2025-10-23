"""
Upload simplified tools to VAPI via API

Usage:
  python upload_tools_to_vapi.py YOUR_VAPI_API_KEY YOUR_WEBHOOK_URL
"""

import json
import requests
import sys
import time

def upload_tools(api_key, webhook_url):
    """Upload all tools to VAPI"""

    # Load tool definitions
    with open('config/vapi-tools-simplified.json', 'r') as f:
        config = json.load(f)

    tools = config['tools']

    print("="*60)
    print("VAPI Tool Upload Script - Simplified System")
    print("="*60)
    print(f"Tools to upload: {len(tools)}")
    print(f"Webhook URL: {webhook_url}")
    print("="*60)
    print()

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    created_tools = []
    failed_tools = []

    for i, tool in enumerate(tools, 1):
        tool_name = tool['function']['name']

        # Update webhook URL
        tool['server']['url'] = f"{webhook_url}/webhook"

        print(f"{i:2d}. Creating {tool_name:25s}...", end=" ")

        try:
            # Create tool via VAPI API
            response = requests.post(
                'https://api.vapi.ai/tool',
                headers=headers,
                json=tool,
                timeout=10
            )

            if response.status_code in [200, 201]:
                tool_id = response.json().get('id')
                created_tools.append({
                    'name': tool_name,
                    'id': tool_id
                })
                print(f"✓ (ID: {tool_id})")
            else:
                failed_tools.append({
                    'name': tool_name,
                    'error': f"HTTP {response.status_code}: {response.text[:100]}"
                })
                print(f"✗ Error: {response.status_code}")
                print(f"    {response.text[:200]}")

        except requests.exceptions.RequestException as e:
            failed_tools.append({
                'name': tool_name,
                'error': str(e)
            })
            print(f"✗ Error: {e}")

        # Rate limiting - be nice to the API
        time.sleep(0.5)

    print()
    print("="*60)
    print("Upload Complete")
    print("="*60)
    print(f"✓ Successfully created: {len(created_tools)}/{len(tools)} tools")
    if failed_tools:
        print(f"✗ Failed: {len(failed_tools)}/{len(tools)} tools")
    print()

    if created_tools:
        print("Created Tools:")
        print("-" * 60)
        for tool in created_tools:
            print(f"  ✓ {tool['name']:25s} → {tool['id']}")
        print()

    if failed_tools:
        print("Failed Tools:")
        print("-" * 60)
        for tool in failed_tools:
            print(f"  ✗ {tool['name']:25s}")
            print(f"    Error: {tool['error']}")
        print()

    # Save tool IDs to file for reference
    if created_tools:
        output_file = 'config/vapi-tool-ids.json'
        with open(output_file, 'w') as f:
            json.dump(created_tools, f, indent=2)
        print(f"Tool IDs saved to: {output_file}")
        print()

    print("="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Go to https://dashboard.vapi.ai")
    print("2. Open your assistant")
    print("3. Go to 'Tools' section")
    print("4. Click 'Add Tool'")
    print("5. Select each of the 15 tools created above")
    print("6. Save assistant")
    print()
    print("7. Update system prompt:")
    print("   Copy contents of: config/system-prompt-simplified.md")
    print("   Paste into assistant's system prompt field")
    print()
    print("8. Test with a call!")
    print("="*60)

    return created_tools, failed_tools

def main():
    if len(sys.argv) != 3:
        print("="*60)
        print("VAPI Tool Upload Script")
        print("="*60)
        print()
        print("Usage:")
        print("  python upload_tools_to_vapi.py YOUR_VAPI_API_KEY YOUR_WEBHOOK_URL")
        print()
        print("Example:")
        print("  python upload_tools_to_vapi.py sk_live_abc123... https://your-domain.com")
        print()
        print("Arguments:")
        print("  YOUR_VAPI_API_KEY  - Your VAPI API key (starts with sk_)")
        print("  YOUR_WEBHOOK_URL   - Your server's webhook URL")
        print()
        print("Get your VAPI API key:")
        print("  1. Go to https://dashboard.vapi.ai")
        print("  2. Click your profile (top right)")
        print("  3. Go to 'API Keys'")
        print("  4. Copy your private key")
        print()
        sys.exit(1)

    api_key = sys.argv[1]
    webhook_url = sys.argv[2].rstrip('/')

    # Validate inputs
    if not api_key.startswith('sk_'):
        print("Error: VAPI API key should start with 'sk_'")
        print(f"You provided: {api_key[:10]}...")
        sys.exit(1)

    if not webhook_url.startswith('http'):
        print("Error: Webhook URL should start with 'http://' or 'https://'")
        print(f"You provided: {webhook_url}")
        sys.exit(1)

    # Confirm before proceeding
    print()
    print("Ready to upload 15 tools to VAPI")
    print(f"Webhook URL: {webhook_url}/webhook")
    print()
    response = input("Continue? [y/N]: ")

    if response.lower() not in ['y', 'yes']:
        print("Cancelled.")
        sys.exit(0)

    print()
    created, failed = upload_tools(api_key, webhook_url)

    # Exit code
    sys.exit(0 if not failed else 1)

if __name__ == "__main__":
    main()

# Architecture Overview

## Core services
- **Business Profile Service**: Loads business identity, hours, and operational rules.
- **Menu Service**: Loads menu JSON and supports updates.
- **Order Service**: Creates and stores orders in SQLite.

## Integrations
- **Vapi.ai**: Tool webhooks at `/webhook/vapi`.
- **Twilio**: SMS receipts and fallback notifications.
- **ElevenLabs**: Text-to-speech endpoint for previews.

## Tool design
Tools are intentionally small and deterministic. The assistant should call these tools to:
1. Check hours.
2. Fetch business profile and menu.
3. Price cart.
4. Create order.
5. Send receipt via SMS.

## Extending to new businesses
Replace `data/business_profile.json` and `data/menu.json` with the new business data. The assistant tools stay the same, but the menu and rules adapt.

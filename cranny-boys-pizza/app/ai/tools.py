"""
Claude AI tool definitions for the Cranny Boys Pizza ordering system.
These are the tools Claude uses to interact with the shop system.
"""

ORDERING_TOOLS = [
    {
        "name": "check_shop_open",
        "description": "Check if the shop is currently open and accepting orders. Always call this at the start of an ordering session.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_caller_context",
        "description": "Get information about the customer — their name, order history, and favourite items. Call this at the start to personalise the experience.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Customer's phone number in E.164 format (e.g. +61412345678)",
                },
            },
            "required": ["phone_number"],
        },
    },
    {
        "name": "search_menu",
        "description": "Search for menu items by name or description. Use this when the customer mentions a food item to get the exact menu entry with price.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What the customer said they want (e.g. 'large hawaiian pizza', 'carbonara pasta', 'wings')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "add_to_cart",
        "description": "Add one or more items to the customer's cart. For pizzas, always specify size. For half/half pizzas set half_half=true and provide half1 and half2 names. For pastas specify pasta_type. For wings specify sauce.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "description": "List of items to add",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Menu item name"},
                            "size": {
                                "type": "string",
                                "enum": ["small", "medium", "large", "family", "jumbo"],
                                "description": "Pizza size (required for pizzas)",
                            },
                            "half_half": {
                                "type": "boolean",
                                "description": "True if this is a half/half pizza",
                                "default": False,
                            },
                            "half1": {
                                "type": "string",
                                "description": "Name of the first half pizza (for half/half orders)",
                            },
                            "half2": {
                                "type": "string",
                                "description": "Name of the second half pizza (for half/half orders)",
                            },
                            "pasta_type": {
                                "type": "string",
                                "enum": ["spaghetti", "penne", "fettuccine", "rigatoni"],
                                "description": "Pasta type for pasta dishes (default: spaghetti)",
                            },
                            "sauce": {
                                "type": "string",
                                "description": "Sauce choice for Wings (garlic butter, honey mustard, BBQ, buffalo, sweet chilli, hot & spicy)",
                            },
                            "quantity": {"type": "integer", "description": "How many (default 1)", "default": 1},
                            "notes": {"type": "string", "description": "Special instructions"},
                        },
                        "required": ["name"],
                    },
                },
            },
            "required": ["items"],
        },
    },
    {
        "name": "view_cart",
        "description": "Show the customer's current cart with all items and the running total.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "edit_cart_item",
        "description": "Edit any property of an item already in the cart (size, half_half, half1, half2, pasta_type, sauce, quantity, etc). Use the item index from view_cart.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_index": {
                    "type": "integer",
                    "description": "Zero-based index of the item to edit (from view_cart)",
                },
                "changes": {
                    "type": "object",
                    "description": "Properties to change",
                    "properties": {
                        "size": {"type": "string", "enum": ["small", "medium", "large", "family", "jumbo"]},
                        "half_half": {"type": "boolean"},
                        "half1": {"type": "string"},
                        "half2": {"type": "string"},
                        "pasta_type": {"type": "string", "enum": ["spaghetti", "penne", "fettuccine", "rigatoni"]},
                        "sauce": {"type": "string"},
                        "quantity": {"type": "integer"},
                        "notes": {"type": "string"},
                    },
                },
            },
            "required": ["item_index", "changes"],
        },
    },
    {
        "name": "remove_from_cart",
        "description": "Remove an item from the cart by its index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_index": {
                    "type": "integer",
                    "description": "Zero-based index of item to remove",
                },
            },
            "required": ["item_index"],
        },
    },
    {
        "name": "clear_cart",
        "description": "Remove all items from the cart and start fresh.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_order_summary",
        "description": "Get a complete, formatted order summary with all items and the final total including GST. Use this before confirming the order.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "set_pickup_time",
        "description": "Let the customer specify when they want to pick up (ASAP or a specific time).",
        "input_schema": {
            "type": "object",
            "properties": {
                "pickup_time": {
                    "type": "string",
                    "description": "'asap' or a time string like '6:30pm'",
                },
            },
            "required": ["pickup_time"],
        },
    },
    {
        "name": "create_order",
        "description": "Finalise and save the order to the system. Only call this AFTER the customer has confirmed all items and the total. Returns an order number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's name for the order (optional)",
                },
                "pickup_time": {
                    "type": "string",
                    "description": "When they want to pick up ('asap' or time)",
                    "default": "asap",
                },
            },
            "required": [],
        },
    },
    {
        "name": "repeat_last_order",
        "description": "Repeat the customer's previous order exactly as it was. Confirm with the customer first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phone_number": {
                    "type": "string",
                    "description": "Customer's phone number",
                },
            },
            "required": ["phone_number"],
        },
    },
    {
        "name": "send_confirmation",
        "description": "Send an SMS or WhatsApp confirmation to the customer with their order details and order number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID to send confirmation for"},
                "channel": {
                    "type": "string",
                    "enum": ["sms", "whatsapp"],
                    "description": "How to send the confirmation",
                },
            },
            "required": ["order_id"],
        },
    },
]

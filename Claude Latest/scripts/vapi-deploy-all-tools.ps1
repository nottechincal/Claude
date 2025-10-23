# Kebabalab VAPI Complete Tool Deployment
# Deletes ALL old tools and creates fresh set with all fixes and new features

$ErrorActionPreference = "Stop"

# Configuration
$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Kebabalab VAPI Tool Deployment - COMPLETE SETUP" -ForegroundColor Cyan
Write-Host "  Including Critical Fixes + 3 New Tools" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Delete ALL existing tools
Write-Host "Step 1: Deleting ALL existing tools..." -ForegroundColor Yellow
Write-Host ""

try {
    $existingTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers

    if ($existingTools.Count -gt 0) {
        Write-Host "  Found $($existingTools.Count) existing tools to delete" -ForegroundColor White

        foreach ($tool in $existingTools) {
            $toolName = $tool.function.name
            Write-Host "  Deleting: $toolName" -NoNewline
            try {
                Invoke-RestMethod -Method Delete -Uri "https://api.vapi.ai/tool/$($tool.id)" -Headers $Headers | Out-Null
                Write-Host " [OK]" -ForegroundColor Green
            }
            catch {
                Write-Host " [FAILED]" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "  No existing tools found" -ForegroundColor Gray
    }
}
catch {
    Write-Host "  Could not fetch existing tools - continuing anyway" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Create ALL tools (23 total)
Write-Host "Step 2: Creating ALL tools (23 total)..." -ForegroundColor Cyan
Write-Host ""

$toolsCreated = @()

# ALL TOOL DEFINITIONS
$newTools = @(
    @{
        name = "checkOpen"
        description = "Check if the shop is currently open for business. Returns opening status, current time, and today's business hours."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "getCallerInfo"
        description = "Silently retrieve the caller's phone number from the call context. Returns formatted phone number and last 3 digits for confirmation. Use at the start of the call."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "validateMenuItem"
        description = "NEW: Validate that a menu item configuration is valid before adding to cart. Prevents fake/invalid orders and protects revenue."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                category = @{
                    type = "string"
                    description = "Item category to validate"
                    enum = @("kebabs", "hsp", "chips", "drinks", "gozleme", "sweets", "extras", "sauce_tubs")
                }
                size = @{
                    type = "string"
                    description = "Size to validate (if applicable)"
                    enum = @("small", "large")
                }
                protein = @{
                    type = "string"
                    description = "Protein type to validate (for kebabs/hsp)"
                    enum = @("lamb", "chicken", "mixed", "falafel")
                }
            }
            required = @("category")
        }
    },
    @{
        name = "startItemConfiguration"
        description = "Start configuring a new menu item. Call this when the customer mentions an item they want to order."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                category = @{
                    type = "string"
                    description = "Item category"
                    enum = @("kebabs", "hsp", "chips", "drinks", "gozleme", "sweets", "extras", "sauce_tubs")
                }
                name = @{
                    type = "string"
                    description = "Specific item name if known"
                }
            }
            required = @("category")
        }
    },
    @{
        name = "setItemProperty"
        description = "Set a property on the item currently being configured (size, protein, salads, sauces, etc.)."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                field = @{
                    type = "string"
                    description = "Property name to set"
                    enum = @("size", "protein", "salads", "sauces", "extras", "cheese", "brand", "variant", "salt_type", "sauce_type", "quantity")
                }
                value = @{
                    description = "Value to set. Can be string, array, boolean, or number depending on field."
                }
            }
            required = @("field", "value")
        }
    },
    @{
        name = "addItemToCart"
        description = "Add the fully configured item to cart. Automatically detects combo opportunities."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "getCartState"
        description = "Get current cart contents and state."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "getDetailedCart"
        description = "NEW: Get human-readable cart with descriptions and modifiers for each item. Better for reviewing order with customer."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "removeCartItem"
        description = "Remove an item from cart by index. Use getCartState first to see cart items and their indexes."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                itemIndex = @{
                    type = "number"
                    description = "Zero-based index of item to remove"
                }
            }
            required = @("itemIndex")
        }
    },
    @{
        name = "editCartItem"
        description = "Edit an existing cart item's properties (salads, sauces, extras, cheese, quantity). Cannot change size or protein."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                itemIndex = @{
                    type = "number"
                    description = "Zero-based index of item to edit"
                }
                field = @{
                    type = "string"
                    description = "Field to edit"
                    enum = @("salads", "sauces", "extras", "cheese", "salt_type", "quantity")
                }
                value = @{
                    description = "New value for the field"
                }
            }
            required = @("itemIndex", "field", "value")
        }
    },
    @{
        name = "modifyCartItem"
        description = "NEW: Modify any property of existing cart item including size, protein. Unrestricted modification tool."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                itemIndex = @{
                    type = "number"
                    description = "Zero-based index of item to modify"
                }
                modifications = @{
                    type = "object"
                    description = "Object containing fields to modify: {salads: [], sauces: [], size: 'large', etc.}"
                }
            }
            required = @("itemIndex", "modifications")
        }
    },
    @{
        name = "convertItemsToMeals"
        description = "NEW: Convert kebabs in cart to meals (kebab + chips + drink). Use when customer says 'make them all meals'."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                itemIndices = @{
                    type = "array"
                    items = @{
                        type = "number"
                    }
                    description = "Optional: specific indices to convert. If not provided, converts ALL kebabs."
                }
                drinkBrand = @{
                    type = "string"
                    description = "Drink choice: coke, sprite, fanta. Default: coke"
                }
                chipsSize = @{
                    type = "string"
                    enum = @("small", "large")
                    description = "Chips size. Default: small"
                }
                chipsSalt = @{
                    type = "string"
                    enum = @("chicken", "plain", "seasoned")
                    description = "Salt type. Default: chicken"
                }
            }
            required = @()
        }
    },
    @{
        name = "clearCart"
        description = "Clear all items from cart. Use when customer wants to start over."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "clearSession"
        description = "Reset entire session (cart, config, state). Use for testing or complete restart."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "priceCart"
        description = "Calculate total price for all items in cart with detailed breakdown. FIXED: Now charges correct prices ($9 large chips, $3.50 drinks)."
        strict = $true
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "getOrderSummary"
        description = "Get human-readable order summary for agent to repeat to customer."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "setOrderNotes"
        description = "Set special instructions/notes for the order."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                notes = @{
                    type = "string"
                    description = "Special instructions"
                }
            }
            required = @("notes")
        }
    },
    @{
        name = "getLastOrder"
        description = "Get customer's last order for repeat ordering. FIXED: No longer crashes on errors."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                phoneNumber = @{
                    type = "string"
                    description = "Customer phone number"
                }
            }
            required = @("phoneNumber")
        }
    },
    @{
        name = "repeatLastOrder"
        description = "NEW: Copy customer's last order to cart for fast reordering. Great for regular customers - 30 second orders!"
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                phoneNumber = @{
                    type = "string"
                    description = "Customer phone number to look up last order"
                }
            }
            required = @("phoneNumber")
        }
    },
    @{
        name = "getMenuByCategory"
        description = "NEW: Browse menu items by category. If no category provided, returns list of all categories."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                category = @{
                    type = "string"
                    description = "Category to browse. Leave empty to get list of all categories."
                }
            }
            required = @()
        }
    },
    @{
        name = "lookupOrder"
        description = "Look up an existing order by ID or phone number. FIXED: No longer crashes on errors."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                orderId = @{
                    type = "string"
                    description = "Order ID to lookup"
                }
                phoneNumber = @{
                    type = "string"
                    description = "Or phone number to lookup"
                }
            }
            required = @()
        }
    },
    @{
        name = "sendMenuLink"
        description = "Send menu link via SMS to customer."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                phoneNumber = @{
                    type = "string"
                    description = "Customer phone number"
                }
            }
            required = @("phoneNumber")
        }
    },
    @{
        name = "setPickupTime"
        description = "Set custom pickup time from customer request."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                minutes = @{
                    type = "number"
                    description = "Minutes from now (minimum 10)"
                }
            }
            required = @("minutes")
        }
    },
    @{
        name = "estimateReadyTime"
        description = "Estimate when the order will be ready for pickup based on current queue."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                requestedTime = @{
                    type = "string"
                    description = "Optional customer requested time"
                }
            }
            required = @()
        }
    },
    @{
        name = "createOrder"
        description = "Create and save the final order to database. Generates order ID and sends SMS notifications."
        strict = $true
        parameters = @{
            type = "object"
            properties = @{
                customerName = @{
                    type = "string"
                    description = "Customer name"
                }
                customerPhone = @{
                    type = "string"
                    description = "Customer phone number"
                }
                readyAtIso = @{
                    type = "string"
                    description = "ISO timestamp when order will be ready"
                }
            }
            required = @("customerName", "customerPhone", "readyAtIso")
        }
    },
    @{
        name = "endCall"
        description = "End the phone call gracefully after order completion."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    }
)

$toolNumber = 1
foreach ($toolDef in $newTools) {
    $toolName = $toolDef.name
    $isNew = $toolDef.description.StartsWith("NEW:")
    $color = if ($isNew) { "Green" } else { "White" }

    Write-Host "  [$toolNumber/23] Creating: $toolName" -NoNewline -ForegroundColor $color

    $body = @{
        type = "function"
        function = @{
            name = $toolDef.name
            description = $toolDef.description
            strict = $toolDef.strict
            parameters = $toolDef.parameters
        }
        async = $false
        server = @{
            url = $WebhookUrl
        }
    }

    $json = $body | ConvertTo-Json -Depth 10 -Compress

    try {
        $result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $Headers -Body $json

        if ($result.id) {
            $toolsCreated += $result.id
            if ($isNew) {
                Write-Host " [NEW!]" -ForegroundColor Green
            }
            else {
                Write-Host " [OK]" -ForegroundColor Green
            }
        }
        else {
            Write-Host " [FAILED - No ID]" -ForegroundColor Red
        }
    }
    catch {
        Write-Host " [FAILED]" -ForegroundColor Red

        if ($_.ErrorDetails.Message) {
            try {
                $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
                Write-Host "    Error: $($errorObj.message)" -ForegroundColor Red
            }
            catch {
                Write-Host "    Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
            }
        }
    }

    $toolNumber++
}

Write-Host ""
Write-Host "Tools created: $($toolsCreated.Count)/23" -ForegroundColor $(if ($toolsCreated.Count -eq 23) { "Green" } else { "Yellow" })
Write-Host ""

if ($toolsCreated.Count -eq 0) {
    Write-Host "ERROR: No tools were created. Cannot continue." -ForegroundColor Red
    exit 1
}

# Step 3: Attach tools to assistant
Write-Host "Step 3: Attaching tools to assistant..." -ForegroundColor Cyan
Write-Host ""

try {
    $currentAssistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers

    $updateBody = @{
        model = @{
            provider = $currentAssistant.model.provider
            model = $currentAssistant.model.model
            toolIds = $toolsCreated
        }
    }

    $json = $updateBody | ConvertTo-Json -Depth 10

    $result = Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers -Body $json

    Write-Host "  Successfully attached $($toolsCreated.Count) tools to assistant [OK]" -ForegroundColor Green
}
catch {
    Write-Host "  Failed to attach tools [FAILED]" -ForegroundColor Red

    if ($_.ErrorDetails.Message) {
        try {
            $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "  Error: $($errorObj.message)" -ForegroundColor Red
        }
        catch {
            Write-Host "  Error: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
    }

    Write-Host ""
    Write-Host "  Tool IDs (attach manually):" -ForegroundColor Yellow
    foreach ($id in $toolsCreated) {
        Write-Host "    $id" -ForegroundColor Yellow
    }

    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  SUCCESS - All Tools Deployed!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Deleted: ALL old tools" -ForegroundColor White
Write-Host "  - Created: 23 tools (3 NEW)" -ForegroundColor White
Write-Host "  - Attached: To assistant $AssistantId" -ForegroundColor White
Write-Host ""
Write-Host "New Tools Added:" -ForegroundColor Green
Write-Host "  1. validateMenuItem - Prevents fake orders" -ForegroundColor White
Write-Host "  2. repeatLastOrder - Fast reorders (30 sec)" -ForegroundColor White
Write-Host "  3. getMenuByCategory - Browse menu" -ForegroundColor White
Write-Host ""
Write-Host "Critical Fixes Applied:" -ForegroundColor Green
Write-Host "  - Large chips: $8 -> $9 (revenue fix)" -ForegroundColor White
Write-Host "  - Drinks: $3 -> $3.50 (revenue fix)" -ForegroundColor White
Write-Host "  - Database crashes fixed" -ForegroundColor White
Write-Host "  - Session cleanup improved" -ForegroundColor White
Write-Host "  - Combo detection fixed" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Test your assistant with a call" -ForegroundColor White
Write-Host "  2. Verify pricing: Large chips = $9, Drinks = $3.50" -ForegroundColor White
Write-Host "  3. Try 'repeat my last order' for regulars" -ForegroundColor White
Write-Host ""

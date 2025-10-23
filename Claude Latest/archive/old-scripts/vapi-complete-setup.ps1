# Kebabalab VAPI Complete Setup Script
# This script deletes old tools, creates new ones with proper descriptions, and attaches them

$ErrorActionPreference = "Stop"

# Configuration
$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "========================================"
Write-Host "  Kebabalab VAPI Complete Setup"
Write-Host "========================================"
Write-Host ""

# Step 1: Delete old tools
Write-Host "Step 1: Deleting old tools..." -ForegroundColor Cyan
Write-Host ""

$oldToolNames = @(
    "validateItem",
    "validateMenuItems",
    "priceOrder",
    "notifyShop",
    "sendReceipt",
    "sendMenuLink",
    "validateSauceRequest",
    "testConnection",
    "detectCombos",
    "getMenu"
)

try {
    $existingTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers

    foreach ($toolName in $oldToolNames) {
        $tool = $existingTools | Where-Object { $_.function.name -eq $toolName }
        if ($tool) {
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
}
catch {
    Write-Host "  Could not fetch existing tools" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Create new tools with full descriptions
Write-Host "Step 2: Creating new tools..." -ForegroundColor Cyan
Write-Host ""

$toolsCreated = @()

# Tool definitions with full descriptions
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
        name = "startItemConfiguration"
        description = "Start configuring a new menu item. Call this when the customer mentions an item they want to order. Returns what field needs to be configured next."
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
        description = "Set a property on the item currently being configured (size, protein, salads, sauces, extras, etc.). Call multiple times to build up the complete item."
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
        description = "Add the fully configured item to cart. Automatically detects combo opportunities and converts items to combos for better pricing. Returns combo information if detected."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "getCartState"
        description = "Get current cart contents and state. Shows all items, whether an item is being configured, and cart totals."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "priceCart"
        description = "Calculate total price for all items in cart with detailed breakdown. Validates menu items, applies modifiers, and returns pricing with GST. Must be called before estimating ready time."
        strict = $true
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    },
    @{
        name = "estimateReadyTime"
        description = "Estimate when the order will be ready for pickup based on current queue and preparation time. Can accept specific customer time requests."
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
        description = "Create and save the final order to database. Generates order ID, saves customer details, and returns confirmation. Must have customer name, phone, and ready time."
        strict = $true
        parameters = @{
            type = "object"
            properties = @{
                customerName = @{
                    type = "string"
                    description = "Customer name for the order"
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
        description = "End the phone call gracefully after order completion. Use this to terminate the conversation."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    }
)

foreach ($toolDef in $newTools) {
    $toolName = $toolDef.name
    Write-Host "  Creating: $toolName" -NoNewline

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
            Write-Host " [OK]" -ForegroundColor Green
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
        else {
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Tools created: $($toolsCreated.Count)/10" -ForegroundColor $(if ($toolsCreated.Count -eq 10) { "Green" } else { "Yellow" })
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

    Write-Host "  Successfully attached $($toolsCreated.Count) tools [OK]" -ForegroundColor Green
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
    else {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "  Tool IDs (attach manually):" -ForegroundColor Yellow
    foreach ($id in $toolsCreated) {
        Write-Host "    $id" -ForegroundColor Yellow
    }

    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "  SUCCESS - Setup Complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Go to https://dashboard.vapi.ai/assistants" -ForegroundColor White
Write-Host "  2. Open your assistant" -ForegroundColor White
Write-Host "  3. Update system prompt (copy from system-prompt.md)" -ForegroundColor White
Write-Host "  4. Test your assistant!" -ForegroundColor White
Write-Host ""

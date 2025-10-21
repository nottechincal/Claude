# VAPI Tools Setup Script - Fixed Version
# Creates all tools and attaches them to the assistant

$ErrorActionPreference = "Stop"

# Configuration
$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$ServerWebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Kebabalab VAPI Tools Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Webhook URL: $ServerWebhookUrl" -ForegroundColor Yellow
Write-Host "Assistant ID: $AssistantId" -ForegroundColor Yellow
Write-Host ""

# Tool Definitions
$tools = @(
    @{
        type = "function"
        function = @{
            name = "checkOpen"
            description = "Check if the shop is currently open for business. Returns opening status and hours."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "getCallerInfo"
            description = "Silently retrieve caller's phone number from call context. Use at start of call."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "startItemConfiguration"
            description = "Start configuring a new menu item. Call this when customer mentions an item."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{
                    category = @{
                        type = "string"
                        description = "Item category: kebabs, hsp, chips, drinks, gozleme, sweets, extras, sauce_tubs"
                        enum = @("kebabs", "hsp", "chips", "drinks", "gozleme", "sweets", "extras", "sauce_tubs")
                    }
                    name = @{
                        type = "string"
                        description = "Specific item name if known"
                    }
                }
                required = @("category")
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "setItemProperty"
            description = "Set a property on the item currently being configured"
            strict = $true
            parameters = @{
                type = "object"
                properties = @{
                    field = @{
                        type = "string"
                        description = "Property name to set"
                        enum = @("size", "protein", "salads", "sauces", "extras", "cheese", "brand", "variant", "salt_type", "sauce_type", "quantity")
                    }
                    value = @{
                        description = "Value to set"
                    }
                }
                required = @("field", "value")
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "addItemToCart"
            description = "Add the fully configured item to cart. Automatically detects combo opportunities."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "getCartState"
            description = "Get current cart contents and state."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "priceCart"
            description = "Calculate total price for all items in cart with detailed breakdown."
            strict = $true
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "estimateReadyTime"
            description = "Estimate when order will be ready for pickup based on current queue."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{
                    requestedTime = @{
                        type = "string"
                        description = "Optional: Customer's requested time"
                    }
                }
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "createOrder"
            description = "Create and save the final order to database."
            strict = $true
            parameters = @{
                type = "object"
                properties = @{
                    customerName = @{
                        type = "string"
                        description = "Customer's name for the order"
                    }
                    customerPhone = @{
                        type = "string"
                        description = "Customer's phone number"
                    }
                    readyAtIso = @{
                        type = "string"
                        description = "ISO timestamp when order will be ready"
                    }
                }
                required = @("customerName", "customerPhone", "readyAtIso")
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    },
    @{
        type = "function"
        function = @{
            name = "endCall"
            description = "End the phone call gracefully after order completion."
            strict = $false
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{ url = $ServerWebhookUrl }
    }
)

# Delete old tools
Write-Host "Checking for existing tools..." -ForegroundColor Yellow

try {
    $existingTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers

    $oldToolNames = @(
        "validateItem", "validateMenuItems", "priceOrder", "notifyShop",
        "sendReceipt", "sendMenuLink", "validateSauceRequest",
        "testConnection", "detectCombos", "getMenu"
    )

    $toolsToDelete = $existingTools | Where-Object {
        $_.function -and $oldToolNames -contains $_.function.name
    }

    if ($toolsToDelete.Count -gt 0) {
        Write-Host "Found $($toolsToDelete.Count) old tools to delete" -ForegroundColor Yellow

        foreach ($tool in $toolsToDelete) {
            Write-Host "  Deleting: $($tool.function.name)..." -NoNewline
            try {
                Invoke-RestMethod -Method Delete -Uri "https://api.vapi.ai/tool/$($tool.id)" -Headers $Headers | Out-Null
                Write-Host " ✓" -ForegroundColor Green
            }
            catch {
                Write-Host " ✗" -ForegroundColor Red
            }
        }
    }
}
catch {
    Write-Host "Could not check existing tools" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Creating new tools..." -ForegroundColor Cyan
Write-Host ""

# Create tools
$createdToolIds = @()
$createdCount = 0

foreach ($tool in $tools) {
    $toolName = $tool.function.name
    Write-Host "Creating: $toolName..." -NoNewline

    try {
        $json = $tool | ConvertTo-Json -Depth 10 -Compress
        $response = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $Headers -Body $json

        if ($response.id) {
            $createdToolIds += $response.id
            $createdCount++
            Write-Host " ✓" -ForegroundColor Green
        }
        else {
            Write-Host " ✗" -ForegroundColor Red
        }
    }
    catch {
        Write-Host " ✗" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "  Error: $($errorObj.message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "Created: $createdCount/10 tools" -ForegroundColor $(if ($createdCount -eq 10) { "Green" } else { "Yellow" })
Write-Host ""

if ($createdToolIds.Count -eq 0) {
    Write-Host "ERROR: No tools were created!" -ForegroundColor Red
    exit 1
}

# Attach tools to assistant
Write-Host "Attaching tools to assistant..." -ForegroundColor Cyan

try {
    $currentAssistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers

    $updateBody = @{
        model = @{
            provider = $currentAssistant.model.provider
            model = $currentAssistant.model.model
            toolIds = $createdToolIds
        }
    }

    $json = $updateBody | ConvertTo-Json -Depth 10
    $response = Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers -Body $json

    Write-Host "✓ Successfully attached $($createdToolIds.Count) tools to assistant!" -ForegroundColor Green
}
catch {
    Write-Host "✗ Failed to attach tools" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "Error: $($errorObj.message)" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Tool IDs (attach manually):" -ForegroundColor Yellow
    foreach ($id in $createdToolIds) {
        Write-Host "  $id" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✓ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor White
Write-Host "  1. Update system prompt in VAPI dashboard" -ForegroundColor White
Write-Host "  2. Copy content from system-prompt.md" -ForegroundColor White
Write-Host "  3. Test your assistant!" -ForegroundColor White
Write-Host ""

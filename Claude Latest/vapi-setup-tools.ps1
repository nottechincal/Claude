# VAPI Tools Setup Script
# Creates all tools and attaches them to the assistant automatically

$ErrorActionPreference = "Stop"

# === Configuration ===
$ApiKey           = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId      = "320f76b1-140a-412c-b95f-252032911ca3"
$ServerWebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type"  = "application/json"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Kebabalab VAPI Tools Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Webhook URL: $ServerWebhookUrl" -ForegroundColor Yellow
Write-Host "Assistant ID: $AssistantId" -ForegroundColor Yellow
Write-Host ""

# === Tool Definitions ===
$tools = @(
    @{
        type = "function"
        function = @{
            name = "checkOpen"
            description = "Check if the shop is currently open for business. Returns opening status and hours."
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "getCallerInfo"
            description = "Silently retrieve caller's phone number from call context. Use at start of call."
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "startItemConfiguration"
            description = "Start configuring a new menu item. Call this when customer mentions an item."
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
                        description = "Specific item name if known (e.g., 'Chicken Kebab', 'Lamb HSP')"
                    }
                }
                required = @("category")
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "setItemProperty"
            description = "Set a property on the item currently being configured (size, protein, salads, sauces, extras, etc.)"
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
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "addItemToCart"
            description = "Add the fully configured item to cart. Automatically detects combo opportunities."
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "getCartState"
            description = "Get current cart contents and state."
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "priceCart"
            description = "Calculate total price for all items in cart with detailed breakdown."
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "estimateReadyTime"
            description = "Estimate when order will be ready for pickup based on current queue."
            parameters = @{
                type = "object"
                properties = @{
                    requestedTime = @{
                        type = "string"
                        description = "Optional: Customer's requested time (e.g., 'in 30 minutes', '6 PM')"
                    }
                }
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "createOrder"
            description = "Create and save the final order to database."
            parameters = @{
                type = "object"
                properties = @{
                    customerName = @{
                        type = "string"
                        description = "Customer's name for the order"
                    }
                    customerPhone = @{
                        type = "string"
                        description = "Customer's phone number (from getCallerInfo)"
                    }
                    readyAtIso = @{
                        type = "string"
                        description = "ISO timestamp when order will be ready (from estimateReadyTime)"
                    }
                }
                required = @("customerName", "customerPhone", "readyAtIso")
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    },
    @{
        type = "function"
        function = @{
            name = "endCall"
            description = "End the phone call gracefully after order completion."
            parameters = @{
                type = "object"
                properties = @{}
                required = @()
            }
        }
        async = $false
        server = @{
            url = $ServerWebhookUrl
        }
    }
)

# === Delete Old Tools (Optional) ===
Write-Host "Fetching existing tools..." -ForegroundColor Yellow

try {
    $existingTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers

    if ($existingTools -and $existingTools.Count -gt 0) {
        Write-Host "Found $($existingTools.Count) existing tools" -ForegroundColor Yellow

        $toolsToDelete = $existingTools | Where-Object {
            $_.function -and $tools.function.name -contains $_.function.name
        }

        if ($toolsToDelete.Count -gt 0) {
            Write-Host ""
            Write-Host "WARNING: Found $($toolsToDelete.Count) tools with matching names that will be replaced:" -ForegroundColor Red
            foreach ($tool in $toolsToDelete) {
                Write-Host "  - $($tool.function.name)" -ForegroundColor Red
            }

            $response = Read-Host "`nDelete these tools and create new ones? (y/n)"

            if ($response -eq "y" -or $response -eq "Y") {
                Write-Host ""
                Write-Host "Deleting old tools..." -ForegroundColor Yellow

                foreach ($tool in $toolsToDelete) {
                    try {
                        Invoke-RestMethod -Method Delete -Uri "https://api.vapi.ai/tool/$($tool.id)" -Headers $Headers
                        Write-Host "  ✓ Deleted: $($tool.function.name)" -ForegroundColor Green
                    } catch {
                        Write-Host "  ✗ Failed to delete: $($tool.function.name)" -ForegroundColor Red
                    }
                }
            } else {
                Write-Host "Skipping deletion. New tools will be created anyway." -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "No existing tools found" -ForegroundColor Green
    }
} catch {
    Write-Host "Could not fetch existing tools (this is OK if starting fresh)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating Tools" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# === Create Tools ===
$createdToolIds = @()
$createdCount = 0
$failedCount = 0

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
        } else {
            $failedCount++
            Write-Host " ✗ (No ID returned)" -ForegroundColor Red
        }
    } catch {
        $failedCount++
        Write-Host " ✗" -ForegroundColor Red

        if ($_.ErrorDetails.Message) {
            $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Host "    Error: $($errorObj.message)" -ForegroundColor Red
        } else {
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Created: $createdCount" -ForegroundColor Green
Write-Host "Failed:  $failedCount" -ForegroundColor $(if ($failedCount -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($createdToolIds.Count -eq 0) {
    Write-Host "No tools were created. Cannot attach to assistant." -ForegroundColor Red
    exit 1
}

# === Attach Tools to Assistant ===
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Attaching Tools to Assistant" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Attaching $($createdToolIds.Count) tools to assistant..." -NoNewline

try {
    # First, get current assistant config to preserve other settings
    $currentAssistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers

    # Update with new tool IDs
    $updateBody = @{
        model = @{
            provider = $currentAssistant.model.provider
            model = $currentAssistant.model.model
            toolIds = $createdToolIds
        }
    }

    $json = $updateBody | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers -Body $json

    Write-Host " ✓" -ForegroundColor Green
    Write-Host ""
    Write-Host "Successfully attached all tools to assistant!" -ForegroundColor Green

} catch {
    Write-Host " ✗" -ForegroundColor Red
    Write-Host ""
    Write-Host "Failed to attach tools to assistant" -ForegroundColor Red

    if ($_.ErrorDetails.Message) {
        $errorObj = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "Error: $($errorObj.message)" -ForegroundColor Red
    } else {
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    }

    Write-Host ""
    Write-Host "Created Tool IDs (attach manually):" -ForegroundColor Yellow
    foreach ($id in $createdToolIds) {
        Write-Host "  - $id" -ForegroundColor Yellow
    }

    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✓ SETUP COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Go to https://dashboard.vapi.ai" -ForegroundColor White
Write-Host "  2. Open your assistant: $AssistantId" -ForegroundColor White
Write-Host "  3. Update system prompt with content from system-prompt.md" -ForegroundColor White
Write-Host "  4. Test your assistant!" -ForegroundColor White
Write-Host ""
Write-Host "Your tools are ready to use!" -ForegroundColor Green
Write-Host ""

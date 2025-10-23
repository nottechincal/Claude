# Add Cart Modification Tools to VAPI Assistant - FIXED VERSION
# This script adds the 3 new cart modification tools: removeCartItem, editCartItem, clearCart

$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "Adding Cart Modification Tools to VAPI Assistant" -ForegroundColor Cyan
Write-Host "================================================================"

$toolsCreated = @()
$errors = @()

# Tool 1: removeCartItem
Write-Host "`n[1/3] Creating removeCartItem tool..." -ForegroundColor Yellow

$removeCartItemTool = @{
    type = "function"
    async = $false
    function = @{
        name = "removeCartItem"
        description = "Remove an item from the cart by index. Use getCartState first to see cart items and their indexes (0-based)."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                itemIndex = @{
                    type = "number"
                    description = "Zero-based index of item to remove (0 for first item, 1 for second, etc.)"
                }
            }
            required = @("itemIndex")
        }
    }
    server = @{
        url = $WebhookUrl
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "https://api.vapi.ai/tool" -Method Post -Headers $Headers -Body $removeCartItemTool
    $removeCartItemId = $response.id
    Write-Host "  SUCCESS: Created removeCartItem (ID: $removeCartItemId)" -ForegroundColor Green
    $toolsCreated += @{name="removeCartItem"; id=$removeCartItemId}
} catch {
    Write-Host "  ERROR: Failed to create removeCartItem" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    $errors += "removeCartItem creation failed"
}

# Tool 2: editCartItem (FIXED - value parameter uses type: string like setItemProperty)
Write-Host "`n[2/3] Creating editCartItem tool..." -ForegroundColor Yellow

$editCartItemTool = @{
    type = "function"
    async = $false
    function = @{
        name = "editCartItem"
        description = "Edit an existing cart item's properties (salads, sauces, extras, cheese, salt_type, quantity). Cannot change size or protein - remove and re-add instead."
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
                    description = "Field to edit: salads, sauces, extras, cheese, salt_type, quantity"
                    enum = @("salads", "sauces", "extras", "cheese", "salt_type", "quantity")
                }
                value = @{
                    type = "string"
                    description = "New value for the field (string, array as JSON string, or boolean/number as string)"
                }
            }
            required = @("itemIndex", "field", "value")
        }
    }
    server = @{
        url = $WebhookUrl
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "https://api.vapi.ai/tool" -Method Post -Headers $Headers -Body $editCartItemTool
    $editCartItemId = $response.id
    Write-Host "  SUCCESS: Created editCartItem (ID: $editCartItemId)" -ForegroundColor Green
    $toolsCreated += @{name="editCartItem"; id=$editCartItemId}
} catch {
    Write-Host "  ERROR: Failed to create editCartItem" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    $errors += "editCartItem creation failed"
}

# Tool 3: clearCart
Write-Host "`n[3/3] Creating clearCart tool..." -ForegroundColor Yellow

$clearCartTool = @{
    type = "function"
    async = $false
    function = @{
        name = "clearCart"
        description = "Clear all items from cart. Use when customer wants to start over."
        strict = $false
        parameters = @{
            type = "object"
            properties = @{}
            required = @()
        }
    }
    server = @{
        url = $WebhookUrl
    }
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod -Uri "https://api.vapi.ai/tool" -Method Post -Headers $Headers -Body $clearCartTool
    $clearCartId = $response.id
    Write-Host "  SUCCESS: Created clearCart (ID: $clearCartId)" -ForegroundColor Green
    $toolsCreated += @{name="clearCart"; id=$clearCartId}
} catch {
    Write-Host "  ERROR: Failed to create clearCart" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    $errors += "clearCart creation failed"
}

Write-Host "`n================================================================"

if ($errors.Count -gt 0) {
    Write-Host "`nERRORS OCCURRED:" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  - $error" -ForegroundColor Red
    }
    Write-Host "`nPlease create failed tools manually in VAPI dashboard." -ForegroundColor Yellow
    exit 1
}

# Now attach tools to assistant
Write-Host "`nAttaching tools to assistant..." -ForegroundColor Yellow

try {
    # Get current assistant to preserve existing tools
    $assistant = Invoke-RestMethod -Uri "https://api.vapi.ai/assistant/$AssistantId" -Method Get -Headers $Headers

    # Get existing tool IDs
    $existingToolIds = @()
    if ($assistant.model.tools) {
        foreach ($tool in $assistant.model.tools) {
            if ($tool.id) {
                $existingToolIds += $tool.id
            }
        }
    }

    Write-Host "  Found $($existingToolIds.Count) existing tools" -ForegroundColor Cyan

    # Add new tool IDs
    $newToolIds = @()
    foreach ($tool in $toolsCreated) {
        $newToolIds += $tool.id
    }

    $allToolIds = $existingToolIds + $newToolIds

    Write-Host "  Total tools after update: $($allToolIds.Count)" -ForegroundColor Cyan

    # Build tools array for update
    $toolsArray = @()
    foreach ($toolId in $allToolIds) {
        $toolsArray += @{
            type = "function"
            id = $toolId
        }
    }

    # Update ONLY the tools array, preserving rest of model config
    $updateBody = @{
        model = @{
            provider = $assistant.model.provider
            model = $assistant.model.model
            tools = $toolsArray
        }
    }

    # Add other required model fields if they exist
    if ($assistant.model.temperature) { $updateBody.model.temperature = $assistant.model.temperature }
    if ($assistant.model.maxTokens) { $updateBody.model.maxTokens = $assistant.model.maxTokens }
    if ($assistant.model.messages) { $updateBody.model.messages = $assistant.model.messages }

    $updateJson = $updateBody | ConvertTo-Json -Depth 10

    $response = Invoke-RestMethod -Uri "https://api.vapi.ai/assistant/$AssistantId" -Method Patch -Headers $Headers -Body $updateJson -ContentType "application/json"

    Write-Host "  SUCCESS: Tools attached to assistant" -ForegroundColor Green

} catch {
    Write-Host "  ERROR: Failed to attach tools to assistant" -ForegroundColor Red
    Write-Host "  $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n  Tools were created but not attached. Please attach manually:" -ForegroundColor Yellow
    foreach ($tool in $toolsCreated) {
        Write-Host "    - $($tool.name): $($tool.id)" -ForegroundColor Cyan
    }
    exit 1
}

Write-Host "`n================================================================"
Write-Host "SUCCESS! All cart modification tools created and attached!" -ForegroundColor Green
Write-Host "`nTool IDs:" -ForegroundColor Cyan
foreach ($tool in $toolsCreated) {
    Write-Host "  $($tool.name): $($tool.id)"
}

Write-Host "`nTotal tools on assistant: $($allToolIds.Count)" -ForegroundColor Green

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Update VAPI assistant system prompt with config/system-prompt-enterprise.md"
Write-Host "  2. Test cart modifications with real phone call"
Write-Host "  3. Server already has the tools implemented in server_v2.py"

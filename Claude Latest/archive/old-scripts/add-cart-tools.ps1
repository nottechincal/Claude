# Add Cart Modification Tools to VAPI Assistant
# This script adds the 3 new cart modification tools: removeCartItem, editCartItem, clearCart

$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "Adding Cart Modification Tools to VAPI Assistant" -ForegroundColor Cyan
Write-Host "=" * 60

# Tool 1: removeCartItem
Write-Host "`nCreating removeCartItem tool..." -ForegroundColor Yellow

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
        url = "$WebhookUrl"
    }
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://api.vapi.ai/tool" -Method Post -Headers $Headers -Body $removeCartItemTool
$removeCartItemId = $response.id
Write-Host "Created removeCartItem: $removeCartItemId" -ForegroundColor Green

# Tool 2: editCartItem
Write-Host "`nCreating editCartItem tool..." -ForegroundColor Yellow

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
                    description = "New value for the field"
                }
            }
            required = @("itemIndex", "field", "value")
        }
    }
    server = @{
        url = "$WebhookUrl"
    }
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://api.vapi.ai/tool" -Method Post -Headers $Headers -Body $editCartItemTool
$editCartItemId = $response.id
Write-Host "Created editCartItem: $editCartItemId" -ForegroundColor Green

# Tool 3: clearCart
Write-Host "`nCreating clearCart tool..." -ForegroundColor Yellow

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
        url = "$WebhookUrl"
    }
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://api.vapi.ai/tool" -Method Post -Headers $Headers -Body $clearCartTool
$clearCartId = $response.id
Write-Host "Created clearCart: $clearCartId" -ForegroundColor Green

# Get current assistant configuration
Write-Host "`nFetching current assistant configuration..." -ForegroundColor Yellow
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

Write-Host "Found $($existingToolIds.Count) existing tools" -ForegroundColor Cyan

# Add new tool IDs
$allToolIds = $existingToolIds + @($removeCartItemId, $editCartItemId, $clearCartId)

# Update assistant with all tools
Write-Host "`nUpdating assistant with all tools (total: $($allToolIds.Count))..." -ForegroundColor Yellow

$updateBody = @{
    model = @{
        tools = @()
    }
}

foreach ($toolId in $allToolIds) {
    $updateBody.model.tools += @{
        type = "function"
        id = $toolId
    }
}

$updateJson = $updateBody | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod -Uri "https://api.vapi.ai/assistant/$AssistantId" -Method Patch -Headers $Headers -Body $updateJson -ContentType "application/json"

Write-Host "`nSUCCESS! All cart modification tools added and attached to assistant." -ForegroundColor Green
Write-Host "`nTool IDs:" -ForegroundColor Cyan
Write-Host "  removeCartItem: $removeCartItemId"
Write-Host "  editCartItem: $editCartItemId"
Write-Host "  clearCart: $clearCartId"

Write-Host "`nTotal tools on assistant: $($allToolIds.Count)" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Update VAPI assistant system prompt with config/system-prompt-enterprise.md"
Write-Host "  2. Test cart modifications with real phone call"
Write-Host "  3. Run python tests/test_tools_mega.py to validate all functionality"

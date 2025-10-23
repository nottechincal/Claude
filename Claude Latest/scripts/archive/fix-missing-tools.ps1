# Fix the 2 missing tools that failed due to type validation

$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host ""
Write-Host "Creating 2 missing tools..." -ForegroundColor Cyan
Write-Host ""

# Create setItemProperty with proper type array
Write-Host "  Creating: setItemProperty" -NoNewline

$body1 = @{
    type = "function"
    function = @{
        name = "setItemProperty"
        description = "Set a property on the item currently being configured (size, protein, salads, sauces, extras, etc.)."
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
                    description = "Value to set (can be string, array, boolean, or number)"
                }
            }
            required = @("field", "value")
        }
    }
    async = $false
    server = @{
        url = $WebhookUrl
    }
}

$json1 = $body1 | ConvertTo-Json -Depth 10 -Compress
try {
    $result1 = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $Headers -Body $json1
    Write-Host " [OK] ID: $($result1.id)" -ForegroundColor Green
    $tool1Id = $result1.id
}
catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Create editCartItem with proper type array
Write-Host "  Creating: editCartItem" -NoNewline

$body2 = @{
    type = "function"
    function = @{
        name = "editCartItem"
        description = "Edit an existing cart item's properties (salads, sauces, extras, cheese, salt_type, quantity). Cannot change size or protein."
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
    }
    async = $false
    server = @{
        url = $WebhookUrl
    }
}

$json2 = $body2 | ConvertTo-Json -Depth 10 -Compress
try {
    $result2 = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $Headers -Body $json2
    Write-Host " [OK] ID: $($result2.id)" -ForegroundColor Green
    $tool2Id = $result2.id
}
catch {
    Write-Host " [FAILED]" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Adding tools to assistant..." -ForegroundColor Cyan

# Get current assistant
$assistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers

# Add the 2 new tool IDs to existing toolIds
$allToolIds = $assistant.model.toolIds + @($tool1Id, $tool2Id)

# Update assistant
$updateBody = @{
    model = @{
        provider = $assistant.model.provider
        model = $assistant.model.model
        toolIds = $allToolIds
    }
}

$json3 = $updateBody | ConvertTo-Json -Depth 10

try {
    $finalResult = Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers -Body $json3
    Write-Host ""
    Write-Host "SUCCESS! All tools now attached." -ForegroundColor Green
    Write-Host "Total tools: $($allToolIds.Count)" -ForegroundColor Cyan
    Write-Host ""
}
catch {
    Write-Host ""
    Write-Host "Failed to attach tools" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

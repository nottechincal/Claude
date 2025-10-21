$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "Checking for setItemProperty tool..." -ForegroundColor Yellow

# Get all tools
$allTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $headers

# Find setItemProperty
$tool = $allTools | Where-Object { $_.function.name -eq "setItemProperty" }

if ($tool) {
    Write-Host "Found existing setItemProperty, deleting it..." -ForegroundColor Yellow
    Invoke-RestMethod -Method Delete -Uri "https://api.vapi.ai/tool/$($tool.id)" -Headers $headers | Out-Null
    Write-Host "Deleted!" -ForegroundColor Green
}

Write-Host "Creating fixed setItemProperty..." -ForegroundColor Cyan

# Create with proper parameter types
$body = @{
    type = "function"
    function = @{
        name = "setItemProperty"
        description = "Set a property on the item currently being configured (size, protein, salads, sauces, extras, etc.)"
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
            additionalProperties = $false
        }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body

Write-Host "Created setItemProperty successfully!" -ForegroundColor Green
Write-Host "Tool ID: $($result.id)" -ForegroundColor Gray

# Now attach to assistant
Write-Host ""
Write-Host "Updating assistant..." -ForegroundColor Cyan

$assistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $headers

# Add the new tool ID to existing tools
$currentToolIds = $assistant.model.toolIds
if (-not $currentToolIds.Contains($result.id)) {
    $currentToolIds += $result.id
}

$updateBody = @{
    model = @{
        provider = $assistant.model.provider
        model = $assistant.model.model
        toolIds = $currentToolIds
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $headers -Body $updateBody | Out-Null

Write-Host "✓ Fixed and attached!" -ForegroundColor Green
Write-Host ""

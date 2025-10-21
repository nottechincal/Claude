$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

$headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host "Deleting old tools..." -ForegroundColor Yellow

# Delete old tools by name
$oldTools = @("validateItem", "validateMenuItems", "priceOrder", "notifyShop", "sendReceipt", "sendMenuLink", "validateSauceRequest", "testConnection", "detectCombos", "getMenu")

$allTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $headers

foreach ($toolName in $oldTools) {
    $tool = $allTools | Where-Object { $_.function.name -eq $toolName }
    if ($tool) {
        Write-Host "  Deleting $toolName..." -NoNewline
        Invoke-RestMethod -Method Delete -Uri "https://api.vapi.ai/tool/$($tool.id)" -Headers $headers | Out-Null
        Write-Host " Done" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Creating new tools..." -ForegroundColor Cyan
Write-Host ""

$toolIds = @()

# Tool 1: checkOpen
$body = @{
    type = "function"
    function = @{
        name = "checkOpen"
        description = "Check if shop is open"
        strict = $false
        parameters = @{ type = "object"; properties = @{}; required = @() }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: checkOpen" -ForegroundColor Green

# Tool 2: getCallerInfo
$body = @{
    type = "function"
    function = @{
        name = "getCallerInfo"
        description = "Get caller phone number"
        strict = $false
        parameters = @{ type = "object"; properties = @{}; required = @() }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: getCallerInfo" -ForegroundColor Green

# Tool 3: startItemConfiguration
$body = @{
    type = "function"
    function = @{
        name = "startItemConfiguration"
        description = "Start configuring a new menu item"
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                category = @{
                    type = "string"
                    enum = @("kebabs", "hsp", "chips", "drinks", "gozleme", "sweets", "extras", "sauce_tubs")
                }
                name = @{ type = "string" }
            }
            required = @("category")
        }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: startItemConfiguration" -ForegroundColor Green

# Tool 4: setItemProperty
$body = @{
    type = "function"
    function = @{
        name = "setItemProperty"
        description = "Set item property"
        strict = $true
        parameters = @{
            type = "object"
            properties = @{
                field = @{
                    type = "string"
                    enum = @("size", "protein", "salads", "sauces", "extras", "cheese", "brand", "variant", "salt_type", "sauce_type", "quantity")
                }
                value = @{}
            }
            required = @("field", "value")
        }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: setItemProperty" -ForegroundColor Green

# Tool 5: addItemToCart
$body = @{
    type = "function"
    function = @{
        name = "addItemToCart"
        description = "Add item to cart"
        strict = $false
        parameters = @{ type = "object"; properties = @{}; required = @() }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: addItemToCart" -ForegroundColor Green

# Tool 6: getCartState
$body = @{
    type = "function"
    function = @{
        name = "getCartState"
        description = "Get cart state"
        strict = $false
        parameters = @{ type = "object"; properties = @{}; required = @() }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: getCartState" -ForegroundColor Green

# Tool 7: priceCart
$body = @{
    type = "function"
    function = @{
        name = "priceCart"
        description = "Calculate total price"
        strict = $true
        parameters = @{ type = "object"; properties = @{}; required = @() }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: priceCart" -ForegroundColor Green

# Tool 8: estimateReadyTime
$body = @{
    type = "function"
    function = @{
        name = "estimateReadyTime"
        description = "Estimate ready time"
        strict = $false
        parameters = @{
            type = "object"
            properties = @{
                requestedTime = @{ type = "string" }
            }
            required = @()
        }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: estimateReadyTime" -ForegroundColor Green

# Tool 9: createOrder
$body = @{
    type = "function"
    function = @{
        name = "createOrder"
        description = "Create order"
        strict = $true
        parameters = @{
            type = "object"
            properties = @{
                customerName = @{ type = "string" }
                customerPhone = @{ type = "string" }
                readyAtIso = @{ type = "string" }
            }
            required = @("customerName", "customerPhone", "readyAtIso")
        }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: createOrder" -ForegroundColor Green

# Tool 10: endCall
$body = @{
    type = "function"
    function = @{
        name = "endCall"
        description = "End call"
        strict = $false
        parameters = @{ type = "object"; properties = @{}; required = @() }
    }
    async = $false
    server = @{ url = $WebhookUrl }
} | ConvertTo-Json -Depth 10

$result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $headers -Body $body
$toolIds += $result.id
Write-Host "Created: endCall" -ForegroundColor Green

Write-Host ""
Write-Host "Attaching tools to assistant..." -ForegroundColor Cyan

$assistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $headers

$updateBody = @{
    model = @{
        provider = $assistant.model.provider
        model = $assistant.model.model
        toolIds = $toolIds
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $headers -Body $updateBody | Out-Null

Write-Host ""
Write-Host "SUCCESS! All 10 tools created and attached!" -ForegroundColor Green
Write-Host ""
Write-Host "Next: Update system prompt in VAPI dashboard" -ForegroundColor Yellow
Write-Host ""

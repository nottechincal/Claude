param(
    [string]$WebhookUrl,
    [switch]$Force
)

$ApiKey = $env:VAPI_API_KEY

if (-not $ApiKey) {
    Write-Error "VAPI_API_KEY is not set. Export it before running."
    exit 1
}

if (-not $WebhookUrl) {
    Write-Error "WebhookUrl is required. Example: -WebhookUrl https://your-domain/webhook/vapi"
    exit 1
}

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

$tools = @(
    @{ name = "check_open"; description = "Check business hours"; parameters = @{ type = "object"; properties = @{}; required = @() } },
    @{ name = "get_business_profile"; description = "Fetch business profile"; parameters = @{ type = "object"; properties = @{}; required = @() } },
    @{ name = "get_menu"; description = "Fetch current menu"; parameters = @{ type = "object"; properties = @{}; required = @() } },
    @{ name = "price_cart"; description = "Price the current cart"; parameters = @{ type = "object"; properties = @{ cart = @{ type = "object" } }; required = @("cart") } },
    @{ name = "create_order"; description = "Create order"; parameters = @{ type = "object"; properties = @{ customer_name = @{ type = "string" }; customer_phone = @{ type = "string" }; cart = @{ type = "object" }; notes = @{ type = "string" } }; required = @("customer_name", "customer_phone", "cart") } },
    @{ name = "send_receipt_sms"; description = "Send an SMS receipt"; parameters = @{ type = "object"; properties = @{ to = @{ type = "string" }; message = @{ type = "string" } }; required = @("to", "message") } }
)

Write-Host "Fetching existing tools..." -ForegroundColor Yellow
$existingTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers
$existingNames = @{}
foreach ($tool in $existingTools) {
    if ($tool.function -and $tool.function.name) {
        $existingNames[$tool.function.name] = $tool.id
    }
}

if ($Force) {
    foreach ($toolDef in $tools) {
        if ($existingNames.ContainsKey($toolDef.name)) {
            $toolId = $existingNames[$toolDef.name]
            Write-Host "Deleting existing tool: $($toolDef.name)" -ForegroundColor DarkYellow
            Invoke-RestMethod -Method Delete -Uri "https://api.vapi.ai/tool/$toolId" -Headers $Headers | Out-Null
        }
    }
}

$createdToolIds = @()
foreach ($toolDef in $tools) {
    $body = @{
        type = "function"
        function = @{
            name = $toolDef.name
            description = $toolDef.description
            strict = $true
            parameters = $toolDef.parameters
        }
        async = $false
        server = @{ url = $WebhookUrl }
    } | ConvertTo-Json -Depth 10

    Write-Host "Creating tool: $($toolDef.name)" -ForegroundColor Cyan
    $result = Invoke-RestMethod -Method Post -Uri "https://api.vapi.ai/tool" -Headers $Headers -Body $body
    $createdToolIds += $result.id
}

Write-Host "Created tool IDs:" -ForegroundColor Green
$createdToolIds | ForEach-Object { Write-Host "  - $_" }

$outputPath = Join-Path -Path $PSScriptRoot -ChildPath "..\\data\\vapi-tool-ids.json"
$outputPath = Resolve-Path -Path $outputPath
$createdToolIds | ConvertTo-Json | Out-File -FilePath $outputPath -Encoding utf8
Write-Host "Saved tool IDs to $outputPath" -ForegroundColor Green

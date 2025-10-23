<#
.SYNOPSIS
    Deploy simplified tools to VAPI - Remove old tools and upload new ones

.DESCRIPTION
    This script automates the VAPI deployment:
    1. Fetches all existing tools from assistant
    2. Removes all old tools
    3. Uploads 15 new simplified tools
    4. Attaches tools to assistant
    5. Displays summary

.PARAMETER ApiKey
    Your VAPI API key (starts with sk_)

.PARAMETER AssistantId
    Your VAPI assistant ID

.PARAMETER WebhookUrl
    Your webhook URL (e.g., https://your-domain.com)

.EXAMPLE
    .\deploy-vapi-tools.ps1 -ApiKey "sk_live_abc123..." -AssistantId "abc-123-def" -WebhookUrl "https://abc123.ngrok-free.app"

.NOTES
    Requires PowerShell 5.1 or higher
    Internet connection required
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey,

    [Parameter(Mandatory=$true)]
    [string]$AssistantId,

    [Parameter(Mandatory=$true)]
    [string]$WebhookUrl
)

# Configuration
$ErrorActionPreference = "Stop"
$VapiBaseUrl = "https://api.vapi.ai"
$ToolsJsonPath = "config/vapi-tools-simplified.json"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }

# Header
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  VAPI Tool Deployment - Simplified System" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Validate inputs
Write-Info "Validating inputs..."

if (-not $ApiKey.StartsWith("sk_")) {
    Write-Error "Error: API key should start with 'sk_'"
    Write-Error "You provided: $($ApiKey.Substring(0, [Math]::Min(10, $ApiKey.Length)))..."
    exit 1
}

if (-not ($WebhookUrl.StartsWith("http://") -or $WebhookUrl.StartsWith("https://"))) {
    Write-Error "Error: Webhook URL should start with 'http://' or 'https://'"
    Write-Error "You provided: $WebhookUrl"
    exit 1
}

if (-not (Test-Path $ToolsJsonPath)) {
    Write-Error "Error: Tools JSON file not found: $ToolsJsonPath"
    exit 1
}

Write-Success "✓ Inputs validated"
Write-Host ""

# Prepare headers
$headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

# Load new tools configuration
Write-Info "Loading new tools configuration..."
$toolsConfig = Get-Content $ToolsJsonPath -Raw | ConvertFrom-Json
$newTools = $toolsConfig.tools
Write-Success "✓ Loaded $($newTools.Count) tool definitions"
Write-Host ""

# Display configuration
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  Assistant ID: $AssistantId"
Write-Host "  Webhook URL:  $WebhookUrl/webhook"
Write-Host "  Tools to deploy: $($newTools.Count)"
Write-Host ""

# Confirm before proceeding
Write-Warning "⚠️  This will:"
Write-Warning "   1. Remove ALL existing tools from your assistant"
Write-Warning "   2. Upload 15 new simplified tools"
Write-Warning "   3. Attach new tools to your assistant"
Write-Host ""
$confirm = Read-Host "Continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Info "Cancelled by user"
    exit 0
}
Write-Host ""

# Step 1: Get current assistant configuration
Write-Info "Step 1: Fetching assistant configuration..."
try {
    $assistantUrl = "$VapiBaseUrl/assistant/$AssistantId"
    $assistant = Invoke-RestMethod -Uri $assistantUrl -Headers $headers -Method Get
    $currentToolIds = $assistant.model.tools

    if ($currentToolIds -and $currentToolIds.Count -gt 0) {
        Write-Success "✓ Found $($currentToolIds.Count) existing tools attached to assistant"
    } else {
        Write-Info "  No tools currently attached to assistant"
        $currentToolIds = @()
    }
} catch {
    Write-Error "Error fetching assistant: $_"
    Write-Info "Continuing anyway - will only upload new tools"
    $currentToolIds = @()
}
Write-Host ""

# Step 2: Fetch all tools in account
Write-Info "Step 2: Fetching all tools in your VAPI account..."
try {
    $allToolsUrl = "$VapiBaseUrl/tool"
    $allTools = Invoke-RestMethod -Uri $allToolsUrl -Headers $headers -Method Get

    if ($allTools -and $allTools.Count -gt 0) {
        Write-Success "✓ Found $($allTools.Count) total tools in your account"
        Write-Host ""
        Write-Host "  Existing tools:" -ForegroundColor Yellow
        foreach ($tool in $allTools) {
            $toolName = $tool.function.name
            $toolId = $tool.id
            Write-Host "    - $toolName (ID: $toolId)" -ForegroundColor Yellow
        }
    } else {
        Write-Info "  No existing tools found"
        $allTools = @()
    }
} catch {
    Write-Warning "Warning: Could not fetch all tools: $_"
    $allTools = @()
}
Write-Host ""

# Step 3: Delete existing tools
if ($allTools.Count -gt 0) {
    Write-Info "Step 3: Removing old tools..."
    $deletedCount = 0
    $failedCount = 0

    foreach ($tool in $allTools) {
        $toolName = $tool.function.name
        $toolId = $tool.id

        Write-Host "  Deleting: $toolName..." -NoNewline

        try {
            $deleteUrl = "$VapiBaseUrl/tool/$toolId"
            Invoke-RestMethod -Uri $deleteUrl -Headers $headers -Method Delete | Out-Null
            Write-Success " ✓"
            $deletedCount++
            Start-Sleep -Milliseconds 300  # Rate limiting
        } catch {
            Write-Error " ✗ Failed: $_"
            $failedCount++
        }
    }

    Write-Host ""
    Write-Success "✓ Deleted $deletedCount tools"
    if ($failedCount -gt 0) {
        Write-Warning "⚠️  Failed to delete $failedCount tools"
    }
} else {
    Write-Info "Step 3: No tools to delete"
}
Write-Host ""

# Step 4: Upload new tools
Write-Info "Step 4: Uploading 15 new simplified tools..."
$createdTools = @()
$failedTools = @()
$toolNumber = 1

foreach ($tool in $newTools) {
    $toolName = $tool.function.name

    # Update webhook URL
    $tool.server.url = "$WebhookUrl/webhook"

    Write-Host "  $($toolNumber.ToString().PadLeft(2)). Creating $($toolName.PadRight(25))..." -NoNewline

    try {
        $createUrl = "$VapiBaseUrl/tool"
        $body = $tool | ConvertTo-Json -Depth 10
        $response = Invoke-RestMethod -Uri $createUrl -Headers $headers -Method Post -Body $body

        $createdTools += @{
            name = $toolName
            id = $response.id
        }

        Write-Success " ✓ (ID: $($response.id))"
        Start-Sleep -Milliseconds 500  # Rate limiting
    } catch {
        $failedTools += @{
            name = $toolName
            error = $_.Exception.Message
        }
        Write-Error " ✗ Failed"
        Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Red
    }

    $toolNumber++
}

Write-Host ""
Write-Success "✓ Created $($createdTools.Count)/$($newTools.Count) tools"
if ($failedTools.Count -gt 0) {
    Write-Warning "⚠️  Failed to create $($failedTools.Count) tools"
}
Write-Host ""

# Step 5: Attach new tools to assistant
if ($createdTools.Count -gt 0) {
    Write-Info "Step 5: Attaching new tools to assistant..."

    try {
        # Build tool IDs array
        $toolIds = $createdTools | ForEach-Object { $_.id }

        # Update assistant with new tools
        $updateUrl = "$VapiBaseUrl/assistant/$AssistantId"
        $updateBody = @{
            model = @{
                tools = $toolIds
            }
        } | ConvertTo-Json -Depth 10

        Invoke-RestMethod -Uri $updateUrl -Headers $headers -Method Patch -Body $updateBody | Out-Null

        Write-Success "✓ Successfully attached $($toolIds.Count) tools to assistant"
    } catch {
        Write-Error "✗ Failed to attach tools to assistant: $_"
        Write-Warning "You may need to manually attach tools in the VAPI dashboard"
    }
} else {
    Write-Error "Step 5: No tools to attach (all uploads failed)"
}
Write-Host ""

# Step 6: Save tool IDs for reference
if ($createdTools.Count -gt 0) {
    Write-Info "Step 6: Saving tool IDs..."

    $outputPath = "config/vapi-tool-ids.json"
    $createdTools | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8

    Write-Success "✓ Tool IDs saved to: $outputPath"
    Write-Host ""
}

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Deployment Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

if ($allTools.Count -gt 0) {
    Write-Host "Old tools removed:     $deletedCount" -ForegroundColor Yellow
}
Write-Host "New tools created:     $($createdTools.Count)" -ForegroundColor Green
Write-Host "Tools attached:        $($createdTools.Count)" -ForegroundColor Green
if ($failedTools.Count -gt 0) {
    Write-Host "Failed:                $($failedTools.Count)" -ForegroundColor Red
}
Write-Host ""

if ($createdTools.Count -gt 0) {
    Write-Host "Created Tools:" -ForegroundColor Cyan
    Write-Host "-------------------------------------------------------------"
    foreach ($tool in $createdTools) {
        Write-Host "  ✓ $($tool.name.PadRight(30)) → $($tool.id)" -ForegroundColor Green
    }
    Write-Host ""
}

if ($failedTools.Count -gt 0) {
    Write-Host "Failed Tools:" -ForegroundColor Red
    Write-Host "-------------------------------------------------------------"
    foreach ($tool in $failedTools) {
        Write-Host "  ✗ $($tool.name)" -ForegroundColor Red
        Write-Host "    Error: $($tool.error)" -ForegroundColor Red
    }
    Write-Host ""
}

# Next steps
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Update system prompt:" -ForegroundColor Yellow
Write-Host "   - Go to https://dashboard.vapi.ai" -ForegroundColor White
Write-Host "   - Open assistant: $AssistantId" -ForegroundColor White
Write-Host "   - Copy contents of: config/system-prompt-simplified.md" -ForegroundColor White
Write-Host "   - Paste into 'System Prompt' field" -ForegroundColor White
Write-Host "   - Save assistant" -ForegroundColor White
Write-Host ""
Write-Host "2. Test the deployment:" -ForegroundColor Yellow
Write-Host "   - Call your VAPI phone number" -ForegroundColor White
Write-Host "   - Order: Chicken kebab meal with Coke" -ForegroundColor White
Write-Host "   - Say: Can you make the chips large?" -ForegroundColor White
Write-Host "   - Expected: Updates in <5 seconds, price = `$25" -ForegroundColor White
Write-Host ""
Write-Host "3. Monitor server logs:" -ForegroundColor Yellow
Write-Host "   - Check: logs/kebabalab_production.log" -ForegroundColor White
Write-Host "   - Look for: No errors, 8-12 tool calls per order" -ForegroundColor White
Write-Host ""

if ($createdTools.Count -eq $newTools.Count -and $failedTools.Count -eq 0) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Success "  ✓ DEPLOYMENT SUCCESSFUL!"
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Success "All 15 tools deployed successfully!"
    Write-Success "Your simplified system is ready to use."
    Write-Host ""
    exit 0
} else {
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Warning "  ⚠️  DEPLOYMENT COMPLETED WITH WARNINGS"
    Write-Host "============================================================" -ForegroundColor Yellow
    Write-Host ""
    Write-Warning "Some tools failed to deploy. Review errors above."
    Write-Host ""
    exit 1
}

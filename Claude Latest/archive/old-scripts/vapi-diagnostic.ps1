# VAPI Configuration Diagnostic Script
# Checks what tools are currently attached to your assistant

$ErrorActionPreference = "Stop"

# === Configuration ===
$ApiKey           = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId      = "320f76b1-140a-412c-b95f-252032911ca3"

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type"  = "application/json"
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VAPI Assistant Diagnostic" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check all tools
Write-Host "Fetching all tools..." -ForegroundColor Yellow
try {
    $allTools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers

    Write-Host "Total tools in account: $($allTools.Count)" -ForegroundColor White
    Write-Host ""

    # Expected new tools
    $expectedNewTools = @(
        "checkOpen",
        "getCallerInfo",
        "startItemConfiguration",
        "setItemProperty",
        "addItemToCart",
        "getCartState",
        "priceCart",
        "estimateReadyTime",
        "createOrder",
        "endCall"
    )

    # Check which tools exist
    Write-Host "NEW TOOLS STATUS:" -ForegroundColor Cyan
    foreach ($toolName in $expectedNewTools) {
        $exists = $allTools | Where-Object { $_.function.name -eq $toolName }
        if ($exists) {
            Write-Host "  ✓ $toolName" -ForegroundColor Green -NoNewline
            Write-Host " (ID: $($exists.id))" -ForegroundColor Gray
        } else {
            Write-Host "  ✗ $toolName" -ForegroundColor Red -NoNewline
            Write-Host " (MISSING!)" -ForegroundColor Red
        }
    }

    # Check for old tools
    Write-Host ""
    Write-Host "OLD TOOLS (should be deleted):" -ForegroundColor Yellow
    $oldTools = @("validateItem", "validateMenuItems", "priceOrder", "notifyShop", "sendReceipt", "sendMenuLink", "validateSauceRequest", "testConnection", "detectCombos")

    $foundOldTools = $false
    foreach ($toolName in $oldTools) {
        $exists = $allTools | Where-Object { $_.function.name -eq $toolName }
        if ($exists) {
            $foundOldTools = $true
            Write-Host "  ⚠ $toolName" -ForegroundColor Red -NoNewline
            Write-Host " (ID: $($exists.id)) - DELETE THIS!" -ForegroundColor Red
        }
    }

    if (-not $foundOldTools) {
        Write-Host "  None found (Good!)" -ForegroundColor Green
    }

} catch {
    Write-Host "Failed to fetch tools!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan

# Check assistant configuration
Write-Host "Fetching assistant configuration..." -ForegroundColor Yellow
try {
    $assistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers

    Write-Host "Assistant Name: $($assistant.name)" -ForegroundColor White
    Write-Host ""

    Write-Host "TOOLS ATTACHED TO ASSISTANT:" -ForegroundColor Cyan

    if ($assistant.model.toolIds) {
        Write-Host "  Total: $($assistant.model.toolIds.Count)" -ForegroundColor White
        Write-Host ""

        # Get details for each tool
        foreach ($toolId in $assistant.model.toolIds) {
            $tool = $allTools | Where-Object { $_.id -eq $toolId }
            if ($tool) {
                $toolName = $tool.function.name

                # Check if it's a new tool
                if ($expectedNewTools -contains $toolName) {
                    Write-Host "  ✓ $toolName" -ForegroundColor Green -NoNewline
                    Write-Host " (NEW - Good!)" -ForegroundColor Green
                } elseif ($oldTools -contains $toolName) {
                    Write-Host "  ✗ $toolName" -ForegroundColor Red -NoNewline
                    Write-Host " (OLD - REMOVE THIS!)" -ForegroundColor Red
                } else {
                    Write-Host "  ? $toolName" -ForegroundColor Yellow -NoNewline
                    Write-Host " (Unknown)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ? Tool ID: $toolId" -ForegroundColor Yellow -NoNewline
                Write-Host " (Tool not found)" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "  NO TOOLS ATTACHED!" -ForegroundColor Red
    }

} catch {
    Write-Host "Failed to fetch assistant!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DIAGNOSIS SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Count new tools
$newToolsCount = 0
foreach ($toolName in $expectedNewTools) {
    $exists = $allTools | Where-Object { $_.function.name -eq $toolName }
    if ($exists) { $newToolsCount++ }
}

# Count old tools attached
$oldToolsAttachedCount = 0
if ($assistant.model.toolIds) {
    foreach ($toolId in $assistant.model.toolIds) {
        $tool = $allTools | Where-Object { $_.id -eq $toolId }
        if ($tool -and ($oldTools -contains $tool.function.name)) {
            $oldToolsAttachedCount++
        }
    }
}

# Count new tools attached
$newToolsAttachedCount = 0
if ($assistant.model.toolIds) {
    foreach ($toolId in $assistant.model.toolIds) {
        $tool = $allTools | Where-Object { $_.id -eq $toolId }
        if ($tool -and ($expectedNewTools -contains $tool.function.name)) {
            $newToolsAttachedCount++
        }
    }
}

if ($newToolsCount -eq 10) {
    Write-Host "✓ All 10 new tools exist" -ForegroundColor Green
} else {
    Write-Host "✗ Only $newToolsCount/10 new tools exist" -ForegroundColor Red
    Write-Host "  → Run vapi-setup-tools.ps1 to create missing tools" -ForegroundColor Yellow
}

if ($newToolsAttachedCount -eq 10) {
    Write-Host "✓ All 10 new tools attached to assistant" -ForegroundColor Green
} else {
    Write-Host "✗ Only $newToolsAttachedCount/10 new tools attached" -ForegroundColor Red
    Write-Host "  → Run vapi-setup-tools.ps1 to attach missing tools" -ForegroundColor Yellow
}

if ($oldToolsAttachedCount -gt 0) {
    Write-Host "✗ $oldToolsAttachedCount old tools still attached!" -ForegroundColor Red
    Write-Host "  → These need to be removed!" -ForegroundColor Yellow
} else {
    Write-Host "✓ No old tools attached" -ForegroundColor Green
}

Write-Host ""

if ($newToolsCount -eq 10 -and $newToolsAttachedCount -eq 10 -and $oldToolsAttachedCount -eq 0) {
    Write-Host "🎉 CONFIGURATION IS CORRECT!" -ForegroundColor Green
    Write-Host ""
    Write-Host "If assistant still not working, check:" -ForegroundColor Yellow
    Write-Host "  1. System prompt is updated (copy from system-prompt.md)" -ForegroundColor White
    Write-Host "  2. Server is running (python server_v2.py)" -ForegroundColor White
    Write-Host "  3. Ngrok is running and URL matches tools" -ForegroundColor White
} else {
    Write-Host "⚠ CONFIGURATION HAS ISSUES!" -ForegroundColor Red
    Write-Host ""
    Write-Host "RECOMMENDED FIX:" -ForegroundColor Yellow
    Write-Host "  Run: ./vapi-setup-tools.ps1" -ForegroundColor White
    Write-Host "  This will create and attach all new tools automatically." -ForegroundColor White
}

Write-Host ""

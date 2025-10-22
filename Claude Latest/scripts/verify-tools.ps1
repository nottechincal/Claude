# Verify all deployed tools

$ApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

Write-Host ""
Write-Host "Checking deployed tools..." -ForegroundColor Cyan
Write-Host ""

$tools = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/tool" -Headers $Headers

Write-Host "Total tools deployed: $($tools.Count)" -ForegroundColor Green
Write-Host ""
Write-Host "Tool List:" -ForegroundColor Yellow

$tools | Sort-Object { $_.function.name } | ForEach-Object {
    $name = $_.function.name
    $desc = $_.function.description
    $isNew = $desc -match "NEW:"

    if ($isNew) {
        Write-Host "  ✓ $name" -ForegroundColor Green -NoNewline
        Write-Host " [NEW]" -ForegroundColor Cyan
    }
    else {
        Write-Host "  ✓ $name" -ForegroundColor White
    }
}

Write-Host ""

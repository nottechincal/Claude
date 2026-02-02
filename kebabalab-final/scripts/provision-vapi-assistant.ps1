param(
    [string]$AssistantId,
    [string]$ToolIdsPath = "../data/vapi-tool-ids.json"
)

$ApiKey = $env:VAPI_API_KEY

if (-not $ApiKey) {
    Write-Error "VAPI_API_KEY is not set. Export it before running."
    exit 1
}

if (-not $AssistantId) {
    $AssistantId = $env:VAPI_ASSISTANT_ID
}

if (-not $AssistantId) {
    Write-Error "AssistantId is required. Provide -AssistantId or set VAPI_ASSISTANT_ID."
    exit 1
}

$toolPath = Join-Path -Path $PSScriptRoot -ChildPath $ToolIdsPath
if (-not (Test-Path $toolPath)) {
    Write-Error "Tool IDs file not found: $toolPath"
    exit 1
}

$toolIds = Get-Content $toolPath | ConvertFrom-Json

$Headers = @{
    "Authorization" = "Bearer $ApiKey"
    "Content-Type" = "application/json"
}

$currentAssistant = Invoke-RestMethod -Method Get -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers

$payload = @{
    name = $currentAssistant.name
    model = $currentAssistant.model
    voice = $currentAssistant.voice
    firstMessage = $currentAssistant.firstMessage
    tools = $toolIds
} | ConvertTo-Json -Depth 10

Write-Host "Updating assistant tools for $AssistantId" -ForegroundColor Cyan
Invoke-RestMethod -Method Patch -Uri "https://api.vapi.ai/assistant/$AssistantId" -Headers $Headers -Body $payload
Write-Host "Assistant updated with $($toolIds.Count) tools." -ForegroundColor Green

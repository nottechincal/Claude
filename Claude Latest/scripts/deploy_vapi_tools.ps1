<#
All-in-one VAPI tools deployer (curl-based, robust payload handling).
- Deletes existing tools
- Creates tools from JSON (array OR { "tools": [...] })
- Attaches toolIds to assistant
- Replaces 'YOUR_WEBHOOK_URL' with configured webhook in each payload
- Writes each payload to a UTF-8 temp file and uses --data-binary "@file" to avoid quoting issues
- Optionally updates the assistant system prompt from a local file
#>

param(
  [string]$ToolsJsonPath = "config/vapi-tools-simplified.json",
  [string]$PromptPath    = "config/system-prompt-simplified.md",
  [switch]$UpdatePrompt
)

$ApiKey      = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$AssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$WebhookUrl  = "https://surveyable-natisha-unsacred.ngrok-free.dev"
$Base        = "https://api.vapi.ai"

function Info([string]$m) { Write-Host $m -ForegroundColor Cyan }
function Ok([string]$m)   { Write-Host $m -ForegroundColor Green }
function Warn([string]$m) { Write-Host $m -ForegroundColor Yellow }
function Err([string]$m)  { Write-Host $m -ForegroundColor Red }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  VAPI Tools Deployer (curl-based, v3) " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Info  ("Assistant: " + $AssistantId)
Info  ("Tools JSON: " + $ToolsJsonPath)
Info  ("Webhook   : " + $WebhookUrl)
if ($UpdatePrompt) { Info ("Prompt    : " + $PromptPath) }
Write-Host ""

if ([string]::IsNullOrWhiteSpace($ApiKey)) { Err "API key is required."; exit 1 }
if ([string]::IsNullOrWhiteSpace($AssistantId)) { Err "AssistantId is required."; exit 1 }
if (-not (Test-Path -LiteralPath $ToolsJsonPath)) { Err "Tools JSON not found at: $ToolsJsonPath"; exit 1 }
if ($UpdatePrompt -and -not (Test-Path -LiteralPath $PromptPath)) { Err "Prompt file not found at: $PromptPath"; exit 1 }

# Load tools
$raw = Get-Content -LiteralPath $ToolsJsonPath -Raw
try { $parsed = $raw | ConvertFrom-Json } catch { Err "Failed to parse JSON: $($_.Exception.Message)"; exit 1 }

if ($parsed -is [System.Collections.IEnumerable]) { $tools = @($parsed) }
elseif ($parsed.tools -and $parsed.tools -is [System.Collections.IEnumerable]) { $tools = @($parsed.tools) }
else { Err "Expected JSON array or object with 'tools' array."; exit 1 }

# Fetch current assistant
Info "Fetching current assistant tools..."
$assistantJson = curl.exe -sS -X GET "$Base/assistant/$AssistantId" -H "Authorization: Bearer $ApiKey" -H "Content-Type: application/json"
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($assistantJson)) { Err "Failed to fetch assistant JSON."; exit 1 }
try { $assistant = $assistantJson | ConvertFrom-Json } catch { Err "Assistant JSON parse error."; exit 1 }

$existingToolIds = @()
if ($assistant.tools) { $existingToolIds = @($assistant.tools | ForEach-Object { $_.id }) }

# Delete existing tools
if ($existingToolIds.Count -gt 0) {
  Info ("Deleting " + $existingToolIds.Count + " existing tool(s)...")
  foreach ($tid in $existingToolIds) {
    $null = curl.exe -sS -X DELETE "$Base/tool/$tid" -H "Authorization: Bearer $ApiKey" -H "Content-Type: application/json"
    if ($LASTEXITCODE -eq 0) { Ok ("Deleted tool " + $tid) } else { Warn ("Delete failed for " + $tid) }
  }
} else { Info "No existing tools attached." }

# Create tools (robust payload via temp file)
$createdIds = @()
$created = 0
$failed = 0
Info ("Creating " + $tools.Count + " tool(s)...")

foreach ($tool in $tools) {
  $payload = ($tool | ConvertTo-Json -Depth 100)
  $payload = $payload.Replace("YOUR_WEBHOOK_URL", $WebhookUrl)

  # Write payload to temp file as UTF-8 without BOM
  $tmp = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), ".json")
  [System.IO.File]::WriteAllText($tmp, $payload, (New-Object System.Text.UTF8Encoding($false)))

  $resp = curl.exe --location -sS "$Base/tool" -H "Content-Type: application/json" -H "Authorization: Bearer $ApiKey" --data-binary "@$tmp"
  # Clean up temp file
  Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue

  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($resp)) { $failed++; Err "Create tool failed (no response)."; continue }
  try { $obj = $resp | ConvertFrom-Json } catch { $failed++; Warn "Create tool returned non-JSON."; continue }

  if ($obj.id) {
    $createdIds += $obj.id
    $created++
    $name = $null
    if ($obj.function -and $obj.function.name) { $name = $obj.function.name }
    elseif ($tool.function -and $tool.function.name) { $name = $tool.function.name }
    if (-not $name) { $name = "(unnamed)" }
    Ok ("Created: " + $name + "  (" + $obj.id + ")")
  } else { $failed++; Warn "Tool created but no id returned." }
}

# Attach tools to assistant
if ($createdIds.Count -gt 0) {
  $model = if ($assistant.model) { $assistant.model } else { @{ provider = "openai"; model = "gpt-4o" } }
  $model.toolIds = $createdIds
  $attachObj = @{ model = $model }
  $attachJson = $attachObj | ConvertTo-Json -Depth 10

  $tmpAttach = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), ".json")
  [System.IO.File]::WriteAllText($tmpAttach, $attachJson, (New-Object System.Text.UTF8Encoding($false)))

  $patchResp = curl.exe --location -sS --request PATCH "$Base/assistant/$AssistantId" -H "Authorization: Bearer $ApiKey" -H "Content-Type: application/json" --data-binary "@$tmpAttach"
  Remove-Item -LiteralPath $tmpAttach -ErrorAction SilentlyContinue

  if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($patchResp)) { Ok ("Attached " + $createdIds.Count + " tool(s) to assistant.") }
  else { Warn "Assistant patch failed. Tools created but not attached." }
} else { Warn "No tools created; skipping attach." }

# Update assistant prompt if requested
if ($UpdatePrompt) {
  Info "Updating assistant system prompt..."
  $promptText = Get-Content -LiteralPath $PromptPath -Raw
  $promptPayload = @{ instructions = $promptText }
  $promptJson = $promptPayload | ConvertTo-Json -Depth 5

  $tmpPrompt = [System.IO.Path]::ChangeExtension([System.IO.Path]::GetTempFileName(), ".json")
  [System.IO.File]::WriteAllText($tmpPrompt, $promptJson, (New-Object System.Text.UTF8Encoding($false)))

  $promptResp = curl.exe --location -sS --request PATCH "$Base/assistant/$AssistantId" -H "Authorization: Bearer $ApiKey" -H "Content-Type: application/json" --data-binary "@$tmpPrompt"
  Remove-Item -LiteralPath $tmpPrompt -ErrorAction SilentlyContinue

  if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($promptResp)) { Ok "Assistant prompt updated." }
  else { Warn "Failed to update assistant prompt." }
}

Write-Host ""
if ($failed -eq 0 -and $created -gt 0) { Ok ("Deployment complete: " + $created + " created, " + $failed + " failed."); exit 0 }
else { Warn ("Deployment completed with issues: " + $created + " created, " + $failed + " failed."); exit 1 }

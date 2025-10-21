# vapi-tools-update.ps1
# Updates existing tools with enhanced descriptions and proper settings

 $ErrorActionPreference = "Stop"

# === Config ===
 $ApiKey           = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
 $AssistantId      = "320f76b1-140a-412c-b95f-252032911ca3"
 $ServerWebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev/webhook"

 $Headers = @{
  "Authorization" = "Bearer $ApiKey"
  "Content-Type"  = "application/json"
}

function Get-Json {
  param([string]$Uri)
  try {
    return Invoke-RestMethod -Method Get -Uri $Uri -Headers $Headers
  } catch {
    Write-Host "GET $Uri failed." -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    throw
  }
}

function Patch-Json {
  param([string]$Uri, [hashtable]$Body)
  $json = $Body | ConvertTo-Json -Depth 100
  try {
    return Invoke-RestMethod -Method Patch -Uri $Uri -Headers $Headers -Body $json
  } catch {
    Write-Host "PATCH $Uri failed." -ForegroundColor Red
    if ($_.ErrorDetails.Message) { Write-Host $_.ErrorDetails.Message }
    throw
  }
}

# First, get all existing tools
Write-Host "Fetching existing tools..."
 $toolsResponse = Get-Json -Uri "https://api.vapi.ai/tool"
 $existingTools = @{}

# Create a lookup of existing tools by name
foreach ($tool in $toolsResponse) {
  if ($tool.function) {
    $existingTools[$tool.function.name] = $tool
  }
}

Write-Host "Found $($existingTools.Count) existing tools"

# Enhanced descriptions for updates
 $enhancedDescriptions = @{
  "checkOpen" = "Check if the shop is currently open for business. Returns opening status, current time, and today's business hours."
  "getMenu" = "Retrieve the complete menu or filter by specific category. Returns all available items, prices, and modifiers."
  "getCallerInfo" = "Silently retrieve the caller's phone number from the call context. Returns formatted phone number and last 3 digits for confirmation."
  "priceOrder" = "Calculate the total price for all items in the cart. Validates menu items, applies modifiers, and returns detailed pricing breakdown with GST."
  "estimateReadyTime" = "Estimate when the order will be ready for pickup based on current queue and preparation time. Can accept specific time requests."
  "createOrder" = "Create and save a new order in the system. Generates order ID, saves customer details, and triggers shop notification."
  "sendReceipt" = "Send a detailed SMS receipt to the customer with order details, items, pricing, and pickup time. Requires explicit customer consent."
  "sendMenuLink" = "Send the menu link via SMS to the customer. Auto-detects caller's number if not provided. Used when customer asks for menu."
  "validateMenuItems" = "Validate a list of items against the current menu to ensure availability. Returns list of invalid items if any."
  "validateItem" = "Validate a single menu item by category, name, size, and brand. Checks if item exists and is available with specified options."
  "endCall" = "Signal the end of the phone call. Used to gracefully terminate the conversation after order completion."
  "validateSauceRequest" = "Determine if customer wants sauce included with item or as a separate tub. Returns appropriate interpretation of sauce request."
  "testConnection" = "Test the server connection and API responsiveness. Returns success status and timestamp for debugging."
  "detectCombos" = "Automatically detect and convert eligible items into combo meals for better pricing. Returns updated cart with combo items."
  "notifyShop" = "Send an SMS notification to the shop with complete order details for preparation. Used internally when order is created."
}

# Proper strict/async settings
 $toolSettings = @{
  "checkOpen" = @{ strict=$false; async=$false }
  "getMenu" = @{ strict=$false; async=$false }
  "getCallerInfo" = @{ strict=$false; async=$false }
  "priceOrder" = @{ strict=$true; async=$false }
  "estimateReadyTime" = @{ strict=$false; async=$false }
  "createOrder" = @{ strict=$true; async=$false }
  "sendReceipt" = @{ strict=$true; async=$true }
  "sendMenuLink" = @{ strict=$false; async=$true }
  "validateMenuItems" = @{ strict=$false; async=$false }
  "validateItem" = @{ strict=$false; async=$false }
  "endCall" = @{ strict=$false; async=$false }
  "validateSauceRequest" = @{ strict=$false; async=$false }
  "testConnection" = @{ strict=$false; async=$false }
  "detectCombos" = @{ strict=$false; async=$false }
  "notifyShop" = @{ strict=$true; async=$true }
}

# Update each tool
 $updatedCount = 0
foreach ($toolName in $enhancedDescriptions.Keys) {
  if ($existingTools.ContainsKey($toolName)) {
    $tool = $existingTools[$toolName]
    $settings = $toolSettings[$toolName]
    
    Write-Host "Updating tool: $toolName"
    
    # Create update body WITHOUT the type property
    $updateBody = @{
      async = $settings.async
      function = @{
        name = $tool.function.name
        description = $enhancedDescriptions[$toolName]
        strict = $settings.strict
        parameters = $tool.function.parameters
      }
      server = @{
        url = $ServerWebhookUrl
      }
    }
    
    # If the tool has messages, preserve them
    if ($tool.messages) {
      $updateBody.messages = $tool.messages
    }
    
    try {
      $response = Patch-Json -Uri "https://api.vapi.ai/tool/$($tool.id)" -Body $updateBody
      Write-Host "  Updated successfully"
      $updatedCount++
    } catch {
      Write-Host "  Failed to update: $toolName"
    }
  } else {
    Write-Host "Tool not found: $toolName"
  }
}

Write-Host "Updated $updatedCount tools successfully!"
Write-Host "Done."
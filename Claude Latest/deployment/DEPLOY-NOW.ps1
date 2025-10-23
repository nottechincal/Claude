<#
.SYNOPSIS
    Deploy to YOUR assistant - Ready to run with your credentials

.DESCRIPTION
    Deploys 15 simplified tools to your VAPI assistant
    Removes all old tools and uploads new ones

.NOTES
    Your credentials are already configured below
#>

# Your credentials
$MyApiKey = "4000447a-37e5-4aa6-b7b3-e692bec2706f"
$MyAssistantId = "320f76b1-140a-412c-b95f-252032911ca3"
$MyWebhookUrl = "https://surveyable-natisha-unsacred.ngrok-free.dev"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Deploying to Your VAPI Assistant" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Using your credentials:" -ForegroundColor Yellow
Write-Host "  Assistant ID: $MyAssistantId" -ForegroundColor White
Write-Host "  Webhook URL:  $MyWebhookUrl" -ForegroundColor White
Write-Host ""

# Call the main deployment script
& "$PSScriptRoot\deploy-vapi-tools.ps1" `
    -ApiKey $MyApiKey `
    -AssistantId $MyAssistantId `
    -WebhookUrl $MyWebhookUrl

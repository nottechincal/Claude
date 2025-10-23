<#
.SYNOPSIS
    Windows setup script for Kebabalab VAPI Server

.DESCRIPTION
    Creates necessary directories and verifies dependencies for Windows

.EXAMPLE
    .\setup-windows.ps1
#>

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Kebabalab VAPI Server - Windows Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found" -ForegroundColor Red
    Write-Host "  Please install Python from https://python.org" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check pip
Write-Host "Checking pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "  ✓ pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ pip not found" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create directories
Write-Host "Creating directories..." -ForegroundColor Yellow

$directories = @("data", "logs", "backups", "config")

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Exists: $dir" -ForegroundColor Gray
    }
}
Write-Host ""

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
Write-Host ""

$packages = @("flask", "flask-cors", "python-dotenv")

foreach ($package in $packages) {
    Write-Host "  Installing $package..." -NoNewline
    try {
        pip install $package --quiet 2>&1 | Out-Null
        Write-Host " ✓" -ForegroundColor Green
    } catch {
        Write-Host " ✗" -ForegroundColor Red
        Write-Host "  Warning: Failed to install $package" -ForegroundColor Yellow
    }
}

Write-Host ""

# Copy menu file if needed
if (-not (Test-Path "data\menu.json")) {
    if (Test-Path "menu.json") {
        Write-Host "Copying menu.json to data directory..." -ForegroundColor Yellow
        Copy-Item "menu.json" "data\menu.json"
        Write-Host "  ✓ Menu file copied" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Warning: menu.json not found" -ForegroundColor Yellow
        Write-Host "  You may need to create it in the data directory" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✓ menu.json exists in data directory" -ForegroundColor Green
}
Write-Host ""

# Test database creation
Write-Host "Testing database initialization..." -ForegroundColor Yellow
$pythonCode = @"
import sqlite3
import os
os.makedirs('data', exist_ok=True)
conn = sqlite3.connect('data/orders.db')
conn.close()
"@

try {
    $pythonCode | python 2>&1 | Out-Null
    Write-Host "  ✓ Database can be created" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Database creation failed" -ForegroundColor Red
}
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Directory structure:" -ForegroundColor Yellow
Write-Host "  data/      - Database and menu files" -ForegroundColor White
Write-Host "  logs/      - Server logs" -ForegroundColor White
Write-Host "  backups/   - Database backups" -ForegroundColor White
Write-Host "  config/    - Configuration files" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Make sure menu.json is in the data/ directory" -ForegroundColor White
Write-Host "  2. Run: python server_simplified.py" -ForegroundColor White
Write-Host "  3. Test: python test_chip_upgrade.py" -ForegroundColor White
Write-Host ""
Write-Host "To deploy to VAPI:" -ForegroundColor Yellow
Write-Host "  .\deploy-vapi-tools.ps1 -ApiKey YOUR_KEY -AssistantId YOUR_ID -WebhookUrl YOUR_URL" -ForegroundColor White
Write-Host ""

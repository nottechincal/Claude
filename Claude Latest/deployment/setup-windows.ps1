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

# Check for menu file
Write-Host "Checking for menu file..." -ForegroundColor Yellow
if (Test-Path "..\data\menu.json") {
    Write-Host "  ✓ menu.json found in data directory" -ForegroundColor Green
} else {
    Write-Host "  ⚠  menu.json not found - server will need this file" -ForegroundColor Yellow
    Write-Host "  Location: data\menu.json" -ForegroundColor Yellow
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
Write-Host "  1. Go back to parent directory: cd .." -ForegroundColor White
Write-Host "  2. Run server: python server_simplified.py" -ForegroundColor White
Write-Host "  3. Test: python tests\test_chip_upgrade.py" -ForegroundColor White
Write-Host ""
Write-Host "To deploy to VAPI:" -ForegroundColor Yellow
Write-Host "  cd deployment" -ForegroundColor White
Write-Host "  .\deploy-my-assistant.ps1" -ForegroundColor White
Write-Host ""
Write-Host "[SUCCESS] Setup complete!" -ForegroundColor Green
Write-Host ""

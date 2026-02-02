param(
    [string]$EnvFile = "../.env"
)

if (-not (Test-Path $EnvFile)) {
    Write-Error "Env file not found at $EnvFile"
    exit 1
}

Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^\s*$" -or $_ -match "^#") { return }
    $parts = $_ -split "=", 2
    if ($parts.Count -eq 2) {
        $name = $parts[0].Trim()
        $value = $parts[1].Trim()
        [System.Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

Write-Host "Environment variables loaded into the current session." -ForegroundColor Green

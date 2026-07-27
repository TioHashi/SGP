$ErrorActionPreference = "SilentlyContinue"

Get-Process cloudflared | Stop-Process -Force

$connections = Get-NetTCPConnection -LocalPort 8000 -State Listen
foreach ($connection in $connections) {
  Stop-Process -Id $connection.OwningProcess -Force
}

Write-Host "SGP público desligado."

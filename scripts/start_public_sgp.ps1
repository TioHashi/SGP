$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$cloudflared = Join-Path $projectRoot "tools\cloudflared.exe"
$tmpDir = Join-Path $projectRoot "tmp"
$outLog = Join-Path $tmpDir "cloudflared.out.log"
$errLog = Join-Path $tmpDir "cloudflared.err.log"

New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot "tools") | Out-Null
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

if (-not (Test-Path $python)) {
  throw "Python do ambiente virtual não encontrado em $python"
}

if (-not (Test-Path $cloudflared)) {
  Write-Host "Baixando Cloudflare Tunnel..."
  Invoke-WebRequest `
    -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
    -OutFile $cloudflared
}

$djangoRunning = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $djangoRunning) {
  Start-Process `
    -FilePath $python `
    -ArgumentList "manage.py", "runserver", "127.0.0.1:8000" `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden
  Start-Sleep -Seconds 4
}

$cloudflaredRunning = Get-Process cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflaredRunning) {
  Remove-Item $outLog, $errLog -ErrorAction SilentlyContinue
  Start-Process `
    -FilePath $cloudflared `
    -ArgumentList "tunnel", "--url", "http://127.0.0.1:8000", "--no-autoupdate" `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden
}

$publicUrl = $null
for ($i = 0; $i -lt 35; $i++) {
  Start-Sleep -Seconds 1
  if (Test-Path $errLog) {
    $content = Get-Content $errLog -Raw
    $match = [regex]::Match($content, "https://[-a-zA-Z0-9]+\.trycloudflare\.com")
    if ($match.Success) {
      $publicUrl = $match.Value
      break
    }
  }
}

if (-not $publicUrl) {
  throw "Não foi possível encontrar a URL pública. Veja o log em $errLog"
}

Write-Host ""
Write-Host "SGP local:   http://127.0.0.1:8000"
Write-Host "SGP publico: $publicUrl"
Write-Host ""
Write-Host "Deixe este notebook ligado para o link continuar funcionando."

$ErrorActionPreference = "Stop"

Write-Host "[NEXUS] Starting local server..."
$existing = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($existing) {
  Stop-Process -Id $existing -Force -ErrorAction SilentlyContinue
}

$server = Start-Process -FilePath "npm" -ArgumentList "start" -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

try {
  $health = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/health" -TimeoutSec 8
  if (-not $health.ok) { throw "Server health is not ok." }
} catch {
  Write-Error "Server did not become healthy: $($_.Exception.Message)"
  exit 1
}

Write-Host "[NEXUS] Opening stable public tunnel (localhost.run)..."
ssh -o StrictHostKeyChecking=no -R 80:127.0.0.1:8080 nokey@localhost.run

param(
  [string]$LocalHost = "127.0.0.1",
  [int]$Port = 8080,
  [int]$ReconnectDelaySec = 3
)

$ErrorActionPreference = "Continue"

function Test-LocalHealth {
  param([string]$TargetHost, [int]$Port)
  try {
    $res = Invoke-RestMethod -Uri "http://$TargetHost`:$Port/api/health" -TimeoutSec 6
    return [bool]$res.ok
  } catch {
    return $false
  }
}

Write-Host "[NEXUS] Resilient online tunnel started."
Write-Host "[NEXUS] Local target: http://$LocalHost`:$Port"
Write-Host "[NEXUS] Press Ctrl+C to stop."

while ($true) {
  if (-not (Test-LocalHealth -TargetHost $LocalHost -Port $Port)) {
    Write-Host "[NEXUS] Local API is not healthy. Waiting..."
    Start-Sleep -Seconds $ReconnectDelaySec
    continue
  }

  Write-Host "[NEXUS] Connecting tunnel via localhost.run ..."
  try {
    ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=20 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -R 80:$LocalHost`:$Port nokey@localhost.run
  } catch {
    Write-Host "[NEXUS] Tunnel error: $($_.Exception.Message)"
  }

  Write-Host "[NEXUS] Tunnel disconnected. Reconnecting in $ReconnectDelaySec sec..."
  Start-Sleep -Seconds $ReconnectDelaySec
}

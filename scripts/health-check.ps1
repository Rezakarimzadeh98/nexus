param(
  [string]$Url = "http://127.0.0.1:8080/api/health",
  [int]$Count = 5,
  [int]$TimeoutSec = 8
)

$ok = 0
for ($i = 1; $i -le $Count; $i++) {
  try {
    $res = Invoke-RestMethod -Uri $Url -TimeoutSec $TimeoutSec
    if ($res.ok) {
      $ok++
      Write-Host "[$i/$Count] OK uptime=$([math]::Round($res.uptime, 2))"
    } else {
      Write-Host "[$i/$Count] FAIL not-ok payload"
    }
  } catch {
    Write-Host "[$i/$Count] FAIL $($_.Exception.Message)"
  }
}

Write-Host "success-rate=$ok/$Count"
if ($ok -lt [math]::Ceiling($Count * 0.7)) {
  exit 1
}

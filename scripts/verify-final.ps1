param()

$ErrorActionPreference = "Stop"

function Test-Url {
  param(
    [Parameter(Mandatory = $true)][string]$Url,
    [int]$TimeoutSec = 15
  )

  try {
    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec
    return [PSCustomObject]@{
      url = $Url
      ok = $true
      status = $response.StatusCode
      message = "ok"
    }
  } catch {
    $statusCode = "-"
    try {
      if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        $statusCode = [int]$_.Exception.Response.StatusCode
      }
    } catch {
      $statusCode = "-"
    }

    return [PSCustomObject]@{
      url = $Url
      ok = $false
      status = $statusCode
      message = $_.Exception.Message
    }
  }
}

function Find-HealthyLocalApi {
  param([int[]]$Ports = @(8080, 8081, 8082, 8083, 8084, 8085))

  foreach ($port in $Ports) {
    $url = "http://127.0.0.1:$port/api/health"
    try {
      $res = Invoke-RestMethod -Uri $url -TimeoutSec 3 -Headers @{ "x-api-key" = "nexus-viewer-2026" }
      if ($res.ok -eq $true) {
        return "http://127.0.0.1:$port"
      }
    } catch {
      continue
    }
  }

  return $null
}

Write-Host "[verify] Checking stable public links..."
$stableLinks = @(
  "https://rezakarimzadeh98.github.io/nexus/",
  "https://rezakarimzadeh98.github.io/nexus/live.html",
  "https://github.com/Rezakarimzadeh98/nexus",
  "https://github.com/Rezakarimzadeh98/nexus/issues",
  "https://github.com/Rezakarimzadeh98/nexus/pulls"
)

$results = @()
foreach ($u in $stableLinks) {
  $results += Test-Url -Url $u
}

Write-Host "[verify] Checking local runtime health (optional)..."
$localBase = Find-HealthyLocalApi
if ($localBase) {
  $results += Test-Url -Url "$localBase/api/health" -TimeoutSec 5
} else {
  $results += [PSCustomObject]@{
    url = "local-runtime"
    ok = $false
    status = "-"
    message = "No healthy localhost runtime found on ports 8080-8085"
  }
}

$results | Format-Table -AutoSize

$failedStable = $results | Where-Object { $_.url -in $stableLinks -and -not $_.ok }
if ($failedStable.Count -gt 0) {
  Write-Error "Final verification failed: one or more stable public links are down."
}

Write-Host "[verify] Final verification passed for stable links."
exit 0

param(
    [string]$ApiBaseUrl = "https://scout-ai-app.onrender.com",
    [string]$SamplesPath = (Join-Path $PSScriptRoot "marketplace-qa-samples.json"),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\\reports\\marketplace-qa")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Normalize-BaseUrl {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "ApiBaseUrl cannot be empty."
    }

    return $Value.TrimEnd("/")
}

function Is-GenericValue {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $true
    }

    $normalized = $Value.Trim().ToLowerInvariant()
    if ($normalized -in @("product", "product research", "online", "unknown")) {
        return $true
    }

    return $normalized.Contains("best price in india") -or
        $normalized.Contains("all categories") -or
        $normalized.Contains("electronics online") -or
        $normalized.Contains("electronics shopping") -or
        $normalized.Contains("maintenance") -or
        $normalized.StartsWith("online at ") -or
        $normalized.StartsWith("buy online ")
}

function Test-AnalysisQuality {
    param(
        [pscustomobject]$Report,
        [pscustomobject]$Sample
    )

    $checks = [ordered]@{
        marketplaceMatched = $Report.marketplace -eq $Sample.marketplace
        brandMatched = [string]::IsNullOrWhiteSpace($Sample.expectedBrand) -or $Report.productBrand -eq $Sample.expectedBrand
        nameLooksSpecific = -not (Is-GenericValue $Report.productName)
        brandLooksSpecific = -not (Is-GenericValue $Report.productBrand)
        enoughSources = @($Report.sources).Count -ge 5
        pricingHistoryPresent = @($Report.pricing.history).Count -ge 1
    }

    $failedChecks = @(
        foreach ($check in $checks.GetEnumerator()) {
            if (-not $check.Value) {
                $check.Key
            }
        }
    )

    return [pscustomobject]@{
        passed = $failedChecks.Count -eq 0
        failedChecks = $failedChecks
        checks = $checks
    }
}

$resolvedApiBaseUrl = Normalize-BaseUrl $ApiBaseUrl
$samples = Get-Content -LiteralPath $SamplesPath -Raw | ConvertFrom-Json
$results = New-Object System.Collections.Generic.List[object]

foreach ($sample in $samples) {
    $payload = @{ url = $sample.url } | ConvertTo-Json
    $errorMessage = $null
    $response = $null

    try {
        $response = Invoke-RestMethod -Uri "$resolvedApiBaseUrl/v1/analysis" -Method Post -ContentType "application/json" -Body $payload
        $report = $response.report
        $quality = Test-AnalysisQuality -Report $report -Sample $sample

        $results.Add([pscustomobject]@{
            marketplace = $sample.marketplace
            passed = $quality.passed
            failedChecks = ($quality.failedChecks -join ", ")
            productName = $report.productName
            productBrand = $report.productBrand
            sourceCount = @($report.sources).Count
            historyCount = @($report.pricing.history).Count
            verdict = $report.verdict
            apiSource = $response.source
            url = $sample.url
        })
    } catch {
        $errorMessage = $_.Exception.Message
        $results.Add([pscustomobject]@{
            marketplace = $sample.marketplace
            passed = $false
            failedChecks = "requestFailed"
            productName = ""
            productBrand = ""
            sourceCount = 0
            historyCount = 0
            verdict = ""
            apiSource = ""
            url = $sample.url
            error = $errorMessage
        })
    }
}

$outputRoot = Resolve-Path (Join-Path $OutputDirectory "..") -ErrorAction SilentlyContinue
if (-not $outputRoot) {
    $null = New-Item -ItemType Directory -Path (Split-Path -Parent $OutputDirectory) -Force
}

$null = New-Item -ItemType Directory -Path $OutputDirectory -Force
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputPath = Join-Path $OutputDirectory "marketplace-qa-$timestamp.json"
$results | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $outputPath

$results |
    Sort-Object marketplace |
    Format-Table marketplace, passed, failedChecks, productBrand, productName, sourceCount, historyCount, verdict -AutoSize

Write-Host ""
Write-Host "Saved QA report to $outputPath" -ForegroundColor Green

$failed = @($results | Where-Object { -not $_.passed })
if ($failed.Count -gt 0) {
    throw "$($failed.Count) marketplace QA checks failed."
}

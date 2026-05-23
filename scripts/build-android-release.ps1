param(
    [Parameter(Mandatory = $true)]
    [string]$ApiBaseUrl,

    [ValidateSet("apk", "aab")]
    [string]$BuildTarget = "apk"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Require-ToolchainPath {
    param(
        [string]$Value,
        [string]$Label,
        [string]$Probe
    )

    if (-not $Value) {
        throw "$Label is not configured. Install the toolchain first or set the user environment variable."
    }

    $resolvedProbe = Join-Path $Value $Probe
    if (-not (Test-Path -LiteralPath $resolvedProbe)) {
        throw "$Label is pointing to an invalid location: $Value"
    }

    return $Value
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$androidProject = Join-Path $repoRoot "apps\\mobile\\android"
$javaHome = Require-ToolchainPath -Value ([Environment]::GetEnvironmentVariable("JAVA_HOME", "User")) -Label "JAVA_HOME" -Probe "bin\\java.exe"
$androidSdkRoot = Require-ToolchainPath -Value ([Environment]::GetEnvironmentVariable("ANDROID_HOME", "User")) -Label "ANDROID_HOME" -Probe "platform-tools\\adb.exe"
$cleanupPaths = @(
    (Join-Path $repoRoot "apps\\mobile\\android\\app\\build"),
    (Join-Path $repoRoot "node_modules\\react-native-gesture-handler\\android\\build"),
    (Join-Path $repoRoot "node_modules\\react-native-safe-area-context\\android\\build"),
    (Join-Path $repoRoot "node_modules\\react-native-screens\\android\\build")
)

$env:JAVA_HOME = $javaHome
$env:ANDROID_HOME = $androidSdkRoot
$env:ANDROID_SDK_ROOT = $androidSdkRoot
$env:Path = "$javaHome\\bin;$androidSdkRoot\\platform-tools;$androidSdkRoot\\cmdline-tools\\latest\\bin;$env:Path"

$gradleTask = if ($BuildTarget -eq "aab") { "app:bundleRelease" } else { "app:assembleRelease" }
$artifactPattern = if ($BuildTarget -eq "aab") { "*.aab" } else { "*.apk" }
$artifactRoot = if ($BuildTarget -eq "aab") {
    Join-Path $androidProject "app\\build\\outputs\\bundle\\release"
} else {
    Join-Path $androidProject "app\\build\\outputs\\apk\\release"
}

Push-Location $androidProject
try {
    & .\gradlew.bat --stop | Out-Null

    foreach ($path in $cleanupPaths) {
        if (Test-Path -LiteralPath $path) {
            try {
                Remove-Item -LiteralPath $path -Recurse -Force -ErrorAction Stop
            } catch [System.IO.DirectoryNotFoundException], [System.IO.FileNotFoundException] {
                continue
            }
        }
    }

    & .\gradlew.bat $gradleTask "-PSCOUT_API_BASE_URL=$ApiBaseUrl" "-Pkotlin.incremental=false" "-Dkotlin.compiler.execution.strategy=in-process" "--no-build-cache"
    if ($LASTEXITCODE -ne 0) {
        throw "Gradle exited with code $LASTEXITCODE."
    }

    $artifact = Get-ChildItem -LiteralPath $artifactRoot -Filter $artifactPattern -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $artifact) {
        throw "Release build finished, but no artifact was found in $artifactRoot"
    }

    Write-Host ""
    Write-Host "Release artifact: $($artifact.FullName)" -ForegroundColor Green
} finally {
    Pop-Location
}

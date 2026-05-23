Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Directory {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Download-File {
    param(
        [string]$Url,
        [string]$Destination
    )

    if (Test-Path -LiteralPath $Destination) {
        Write-Host "Using cached file: $Destination"
        return
    }

    Write-Host "Downloading $Url"
    & curl.exe -L --fail --output $Destination $Url
}

function Prepend-UserPathEntries {
    param([string[]]$Entries)

    $currentUserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $parts = @()

    if ($currentUserPath) {
        $parts = $currentUserPath.Split(";") | Where-Object { $_ -and $_.Trim() }
    }

    foreach ($entry in $Entries) {
        if ($parts -notcontains $entry) {
            $parts = @($entry) + $parts
        }
    }

    $updatedPath = ($parts | Select-Object -Unique) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $updatedPath, "User")
    $env:Path = $updatedPath + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine")
}

function Install-Python {
    param(
        [string]$PythonInstaller,
        [string]$PythonDir
    )

    Write-Step "Installing Python 3.11 into $PythonDir"
    Ensure-Directory -Path (Split-Path -Parent $PythonDir)

    $arguments = @(
        "/quiet",
        "InstallAllUsers=0",
        "TargetDir=$PythonDir",
        "PrependPath=0",
        "Include_pip=1",
        "Include_test=0",
        "Include_launcher=0",
        "SimpleInstall=1",
        "Shortcuts=0"
    )

    $process = Start-Process -FilePath $PythonInstaller -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
    if ($process.ExitCode -ne 0) {
        throw "Python installer exited with code $($process.ExitCode)."
    }
}

function Install-Java {
    param(
        [string]$JavaArchive,
        [string]$JavaRoot
    )

    Write-Step "Installing Temurin JDK 17 into $JavaRoot"
    Ensure-Directory -Path $JavaRoot

    $extractDir = Join-Path $JavaRoot "extract"
    if (Test-Path -LiteralPath $extractDir) {
        Remove-Item -LiteralPath $extractDir -Recurse -Force
    }

    Expand-Archive -LiteralPath $JavaArchive -DestinationPath $extractDir -Force

    $jdkFolder = Get-ChildItem -LiteralPath $extractDir -Directory | Select-Object -First 1
    if (-not $jdkFolder) {
        throw "Could not find the extracted JDK folder."
    }

    $finalJdkDir = Join-Path $JavaRoot "temurin-17"
    if (Test-Path -LiteralPath $finalJdkDir) {
        Remove-Item -LiteralPath $finalJdkDir -Recurse -Force
    }

    Move-Item -LiteralPath $jdkFolder.FullName -Destination $finalJdkDir
    Remove-Item -LiteralPath $extractDir -Recurse -Force

    [Environment]::SetEnvironmentVariable("JAVA_HOME", $finalJdkDir, "User")
    $env:JAVA_HOME = $finalJdkDir
}

function Install-AndroidStudio {
    param(
        [string]$StudioArchive,
        [string]$StudioRoot
    )

    Write-Step "Installing Android Studio into $StudioRoot"
    Ensure-Directory -Path (Split-Path -Parent $StudioRoot)

    $extractDir = Join-Path (Split-Path -Parent $StudioRoot) "android-studio-extract"
    if (Test-Path -LiteralPath $extractDir) {
        Remove-Item -LiteralPath $extractDir -Recurse -Force
    }

    Expand-Archive -LiteralPath $StudioArchive -DestinationPath $extractDir -Force

    $extractedStudio = Get-ChildItem -LiteralPath $extractDir -Directory | Select-Object -First 1
    if (-not $extractedStudio) {
        throw "Could not find the extracted Android Studio folder."
    }

    if (Test-Path -LiteralPath $StudioRoot) {
        Remove-Item -LiteralPath $StudioRoot -Recurse -Force
    }

    Move-Item -LiteralPath $extractedStudio.FullName -Destination $StudioRoot
    Remove-Item -LiteralPath $extractDir -Recurse -Force
}

function Install-AndroidCmdlineTools {
    param(
        [string]$CmdlineArchive,
        [string]$SdkRoot
    )

    Write-Step "Installing Android command-line tools into $SdkRoot"
    Ensure-Directory -Path $SdkRoot

    $cmdlineRoot = Join-Path $SdkRoot "cmdline-tools"
    Ensure-Directory -Path $cmdlineRoot

    $stagingDir = Join-Path $SdkRoot "cmdline-tools-staging"
    if (Test-Path -LiteralPath $stagingDir) {
        Remove-Item -LiteralPath $stagingDir -Recurse -Force
    }

    Expand-Archive -LiteralPath $CmdlineArchive -DestinationPath $stagingDir -Force

    $extractedRoot = Join-Path $stagingDir "cmdline-tools"
    if (-not (Test-Path -LiteralPath $extractedRoot)) {
        throw "Could not find the extracted Android command-line tools folder."
    }

    $latestDir = Join-Path $cmdlineRoot "latest"
    if (Test-Path -LiteralPath $latestDir) {
        Remove-Item -LiteralPath $latestDir -Recurse -Force
    }

    Ensure-Directory -Path $latestDir
    Get-ChildItem -LiteralPath $extractedRoot -Force | ForEach-Object {
        Move-Item -LiteralPath $_.FullName -Destination $latestDir
    }

    Remove-Item -LiteralPath $stagingDir -Recurse -Force

    [Environment]::SetEnvironmentVariable("ANDROID_HOME", $SdkRoot, "User")
    [Environment]::SetEnvironmentVariable("ANDROID_SDK_ROOT", $SdkRoot, "User")
    $env:ANDROID_HOME = $SdkRoot
    $env:ANDROID_SDK_ROOT = $SdkRoot
}

function Install-AndroidSdkPackages {
    param(
        [string]$SdkRoot
    )

    Write-Step "Installing Android SDK packages"
    $sdkManager = Join-Path $SdkRoot "cmdline-tools\latest\bin\sdkmanager.bat"
    if (-not (Test-Path -LiteralPath $sdkManager)) {
        throw "sdkmanager.bat was not found at $sdkManager"
    }

    $licenseAnswers = ((1..20) | ForEach-Object { "y" }) -join "`n"
    $licenseAnswers | & $sdkManager --sdk_root=$SdkRoot --licenses | Out-Null

    & $sdkManager --sdk_root=$SdkRoot "platform-tools" "platforms;android-35" "build-tools;35.0.0" | Out-Host
}

$downloadRoot = Join-Path $env:LOCALAPPDATA "ScoutAIToolingCache"
$pythonDir = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311"
$javaRoot = Join-Path $env:LOCALAPPDATA "Programs\Java"
$studioRoot = Join-Path $env:LOCALAPPDATA "Programs\AndroidStudio"
$sdkRoot = Join-Path $env:LOCALAPPDATA "Android\Sdk"

Ensure-Directory -Path $downloadRoot

$pythonInstaller = Join-Path $downloadRoot "python-3.11.9-amd64.exe"
$javaArchive = Join-Path $downloadRoot "temurin17-jdk.zip"
$studioArchive = Join-Path $downloadRoot "android-studio-panda4-patch1-windows.zip"
$cmdlineArchive = Join-Path $downloadRoot "commandlinetools-win-14742923_latest.zip"

Download-File -Url "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -Destination $pythonInstaller
Download-File -Url "https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse" -Destination $javaArchive
Download-File -Url "https://edgedl.me.gvt1.com/android/studio/ide-zips/2025.3.4.7/android-studio-panda4-patch1-windows.zip" -Destination $studioArchive
Download-File -Url "https://dl.google.com/android/repository/commandlinetools-win-14742923_latest.zip" -Destination $cmdlineArchive

Install-Python -PythonInstaller $pythonInstaller -PythonDir $pythonDir
Install-Java -JavaArchive $javaArchive -JavaRoot $javaRoot
Install-AndroidStudio -StudioArchive $studioArchive -StudioRoot $studioRoot
Install-AndroidCmdlineTools -CmdlineArchive $cmdlineArchive -SdkRoot $sdkRoot

Prepend-UserPathEntries -Entries @(
    (Join-Path $pythonDir "Scripts"),
    $pythonDir,
    (Join-Path $env:JAVA_HOME "bin"),
    (Join-Path $sdkRoot "platform-tools"),
    (Join-Path $sdkRoot "cmdline-tools\latest\bin"),
    (Join-Path $studioRoot "bin")
)

Install-AndroidSdkPackages -SdkRoot $sdkRoot

Write-Step "Verification"
& (Join-Path $pythonDir "python.exe") --version
& (Join-Path $env:JAVA_HOME "bin\java.exe") -version
& (Join-Path $sdkRoot "platform-tools\adb.exe") version
Write-Host "Android Studio path: $studioRoot"
Write-Host "Android SDK path: $sdkRoot"

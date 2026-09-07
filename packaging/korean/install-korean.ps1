[CmdletBinding()]
param(
    [string]$OpenMWPath = "",
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeRoot = Join-Path $scriptDir "payload\runtime"
$payloadMod = Join-Path $scriptDir "payload\mods\Morrowind_Korean_ReTranslation"
$configUpdater = Join-Path $scriptDir "install-korean-config.ps1"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$modFolderName = "Morrowind_Korean_ReTranslation"

$requiredRuntimeFiles = @(
    "openmw.exe",
    "avcodec-62.dll",
    "avformat-62.dll",
    "avutil-60.dll",
    "swresample-6.dll",
    "MyGUIEngine.dll",
    "osg.dll",
    "osgDB.dll"
)
$requiredModFiles = @(
    "Morrowind_Korean_ReTranslation.esp",
    "Morrowind_Korean_ReTranslation.cel",
    "Morrowind_Korean_ReTranslation.mrk",
    "Morrowind_Korean_ReTranslation.top"
)
$requiredSubtitleFiles = @(
    "mw_intro.srt",
    "mw_cavern.srt",
    "mw_end.srt",
    "bm_bearhunt1.srt",
    "bm_bearhunt2.srt",
    "bm_ceremony1.srt",
    "bm_ceremony2.srt",
    "bm_endgame.srt",
    "bm_frostgiant1.srt",
    "bm_frostgiant2.srt"
)

function Test-OpenMWInstall([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        return (Test-Path -LiteralPath (Join-Path $full "openmw.exe") -PathType Leaf)
    } catch {
        return $false
    }
}

foreach ($name in $requiredRuntimeFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot $name) -PathType Leaf)) {
        throw "Required matching OpenMW runtime file is missing: $name"
    }
}
foreach ($name in $requiredModFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $payloadMod $name) -PathType Leaf)) {
        throw "Korean translation payload file is missing: $name"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $payloadMod "l10n") -PathType Container)) {
    throw "Korean translation l10n payload is missing: $payloadMod\l10n"
}
foreach ($name in $requiredSubtitleFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $payloadMod "video\$name") -PathType Leaf)) {
        throw "Required Korean video subtitle is missing: $name"
    }
}
if (-not (Test-Path -LiteralPath $configUpdater -PathType Leaf)) {
    throw "Config updater not found: $configUpdater"
}

if ([string]::IsNullOrWhiteSpace($OpenMWPath)) {
    $candidates = New-Object 'System.Collections.Generic.List[string]'
    [void]$candidates.Add($scriptDir)
    [void]$candidates.Add((Split-Path -Parent $scriptDir))

    $uninstallRoots = @(
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )
    foreach ($root in $uninstallRoots) {
        Get-ItemProperty $root -ErrorAction SilentlyContinue | Where-Object {
            $_.DisplayName -like 'OpenMW*' -and -not [string]::IsNullOrWhiteSpace($_.InstallLocation)
        } | ForEach-Object {
            [void]$candidates.Add($_.InstallLocation)
        }
    }

    if ($env:ProgramFiles) {
        Get-ChildItem -LiteralPath $env:ProgramFiles -Directory -Filter 'OpenMW*' -ErrorAction SilentlyContinue | ForEach-Object {
            [void]$candidates.Add($_.FullName)
        }
    }
    if (${env:ProgramFiles(x86)}) {
        Get-ChildItem -LiteralPath ${env:ProgramFiles(x86)} -Directory -Filter 'OpenMW*' -ErrorAction SilentlyContinue | ForEach-Object {
            [void]$candidates.Add($_.FullName)
        }
    }

    $OpenMWPath = $candidates | Where-Object { Test-OpenMWInstall $_ } | Select-Object -First 1
}

if ([string]::IsNullOrWhiteSpace($OpenMWPath)) {
    $OpenMWPath = Read-Host "OpenMW installation folder (the folder containing openmw.exe)"
}

$OpenMWPath = [System.IO.Path]::GetFullPath($OpenMWPath)
if (-not (Test-OpenMWInstall $OpenMWPath)) {
    throw "OpenMW installation not found at: $OpenMWPath"
}

if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $ConfigPath = Join-Path ([Environment]::GetFolderPath('MyDocuments')) "My Games\OpenMW\openmw.cfg"
}
$ConfigPath = [System.IO.Path]::GetFullPath($ConfigPath)
if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
    throw "OpenMW config not found: $ConfigPath`nRun OpenMW once first."
}

$backupDir = Join-Path $OpenMWPath "korean-kr3-backup-$timestamp"
$runtimeBackup = Join-Path $backupDir "runtime"
$modBackup = Join-Path $backupDir "mod"
New-Item -ItemType Directory -Path $runtimeBackup -Force | Out-Null

$newFiles = New-Object 'System.Collections.Generic.List[string]'
$overwrittenFiles = New-Object 'System.Collections.Generic.List[string]'
$runtimeRootFull = [System.IO.Path]::GetFullPath($runtimeRoot).TrimEnd('\')

Write-Host "Backing up and installing the matching OpenMW 0.51.0 Korean runtime set..."
Get-ChildItem -LiteralPath $runtimeRoot -File -Recurse | ForEach-Object {
    $relative = $_.FullName.Substring($runtimeRootFull.Length).TrimStart([char[]]@('\','/'))

    # Do not replace OpenMW's global config with the CI artifact's sample config.
    # Movie fallbacks are managed in the user's openmw.cfg instead.
    if ($relative -ieq "openmw.cfg" -or $relative -ieq "CI-ID.txt") {
        return
    }

    $destination = Join-Path $OpenMWPath $relative
    if (Test-Path -LiteralPath $destination -PathType Leaf) {
        $backup = Join-Path $runtimeBackup $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $backup) -Force | Out-Null
        Copy-Item -LiteralPath $destination -Destination $backup -Force
        [void]$overwrittenFiles.Add($relative)
    } else {
        [void]$newFiles.Add($relative)
    }

    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
}
$newFiles | Set-Content -LiteralPath (Join-Path $backupDir "new-runtime-files.txt") -Encoding UTF8
$overwrittenFiles | Set-Content -LiteralPath (Join-Path $backupDir "overwritten-runtime-files.txt") -Encoding UTF8

$targetModsRoot = Join-Path $OpenMWPath "mods"
$targetMod = Join-Path $targetModsRoot $modFolderName
$legacyTargetMod = Join-Path $targetModsRoot "Morrowind_Korean_ReTranslation_v01"
New-Item -ItemType Directory -Path $targetModsRoot -Force | Out-Null

$hadMod = Test-Path -LiteralPath $targetMod -PathType Container
if ($hadMod) {
    Write-Host "Backing up existing Korean mod folder..."
    Copy-Item -LiteralPath $targetMod -Destination $modBackup -Recurse -Force
    Remove-Item -LiteralPath $targetMod -Recurse -Force
}
if (Test-Path -LiteralPath $legacyTargetMod -PathType Container) {
    Copy-Item -LiteralPath $legacyTargetMod -Destination (Join-Path $backupDir "legacy-mod") -Recurse -Force
    Remove-Item -LiteralPath $legacyTargetMod -Recurse -Force
}

Write-Host "Installing Korean translation data and video subtitles..."
Copy-Item -LiteralPath $payloadMod -Destination $targetMod -Recurse -Force

Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $backupDir "openmw.cfg.user") -Force
Set-Content -LiteralPath (Join-Path $backupDir "config-path.txt") -Value $ConfigPath -Encoding UTF8
Set-Content -LiteralPath (Join-Path $backupDir "had-mod.txt") -Value ($(if ($hadMod) {"1"} else {"0"})) -Encoding ASCII

Write-Host "Updating OpenMW config for Korean data, fonts, and Morrowind movie fallbacks..."
& $configUpdater -OpenMWPath $OpenMWPath -ConfigPath $ConfigPath

foreach ($name in $requiredRuntimeFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $OpenMWPath $name) -PathType Leaf)) {
        throw "Runtime file was not installed correctly: $name"
    }
}
foreach ($name in $requiredSubtitleFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $targetMod "video\$name") -PathType Leaf)) {
        throw "Subtitle was not installed correctly: $name"
    }
}

$marker = @"
OpenMW 0.51.0 Korean Support KR3
Installed: $timestamp
Backup: $backupDir
Runtime: matching Windows runtime set with Korean patches 0001-0005
Video subtitles: 10 UTF-8 SRT files
"@
Set-Content -LiteralPath (Join-Path $OpenMWPath "OPENMW-KOREAN-KR3.txt") -Value $marker -Encoding UTF8

Write-Host ""
Write-Host "OpenMW Korean KR3 installation completed."
Write-Host "OpenMW    : $OpenMWPath"
Write-Host "Korean mod: $targetMod"
Write-Host "Subtitles : $targetMod\video"
Write-Host "Backup    : $backupDir"

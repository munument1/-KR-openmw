[CmdletBinding()]
param(
    [string]$OpenMWPath = "",
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$payloadDir = Join-Path $scriptDir "payload"
$payloadExe = Join-Path $payloadDir "openmw.exe"
$payloadFonts = Join-Path $payloadDir "resources\vfs\fonts"
$modFolderName = "Morrowind_Korean_ReTranslation"
$pluginFileName = "Morrowind_Korean_ReTranslation.esp"
$legacyModFolderName = "Morrowind_Korean_ReTranslation_v01"
$requiredModFiles = @(
    "Morrowind_Korean_ReTranslation.esp",
    "Morrowind_Korean_ReTranslation.cel",
    "Morrowind_Korean_ReTranslation.mrk",
    "Morrowind_Korean_ReTranslation.top"
)
$payloadMod = Join-Path $payloadDir "mods\$modFolderName"
$configUpdater = Join-Path $scriptDir "install-korean-config.ps1"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not (Test-Path -LiteralPath $payloadExe -PathType Leaf)) {
    throw "Korean openmw.exe payload not found: $payloadExe"
}
if (-not (Test-Path -LiteralPath $payloadFonts -PathType Container)) {
    throw "Korean font payload not found: $payloadFonts"
}
foreach ($requiredModFile in $requiredModFiles) {
    $requiredPath = Join-Path $payloadMod $requiredModFile
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Korean translation payload file not found: $requiredPath"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $payloadMod "l10n") -PathType Container)) {
    throw "Korean translation l10n payload not found: $payloadMod\l10n"
}
if (-not (Test-Path -LiteralPath $configUpdater -PathType Leaf)) {
    throw "Config updater not found: $configUpdater"
}

function Test-OpenMWInstall([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        return (Test-Path -LiteralPath (Join-Path $full "openmw.exe") -PathType Leaf)
    } catch {
        return $false
    }
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

$targetExe = Join-Path $OpenMWPath "openmw.exe"
$targetFonts = Join-Path $OpenMWPath "resources\vfs\fonts"
$targetModsRoot = Join-Path $OpenMWPath "mods"
$targetMod = Join-Path $targetModsRoot $modFolderName
$legacyTargetMod = Join-Path $targetModsRoot $legacyModFolderName
New-Item -ItemType Directory -Path $targetFonts -Force | Out-Null
New-Item -ItemType Directory -Path $targetModsRoot -Force | Out-Null

$engineBackup = "$targetExe.korean-backup-$timestamp"
Copy-Item -LiteralPath $targetExe -Destination $engineBackup -Force

Write-Host "Installing Korean OpenMW engine..."
Copy-Item -LiteralPath $payloadExe -Destination $targetExe -Force

Write-Host "Installing Korean font assets..."
Get-ChildItem -LiteralPath $payloadFonts -File | ForEach-Object {
    $destination = Join-Path $targetFonts $_.Name
    if (Test-Path -LiteralPath $destination -PathType Leaf) {
        Copy-Item -LiteralPath $destination -Destination "$destination.korean-backup-$timestamp" -Force
    }
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
}

$modBackup = ""
if (Test-Path -LiteralPath $targetMod -PathType Container) {
    $modBackup = "$targetMod.korean-backup-$timestamp"
    Write-Host "Backing up existing Korean mod folder..."
    Copy-Item -LiteralPath $targetMod -Destination $modBackup -Recurse -Force
    Remove-Item -LiteralPath $targetMod -Recurse -Force
}

$legacyModBackup = ""
if (Test-Path -LiteralPath $legacyTargetMod -PathType Container) {
    $legacyModBackup = "$legacyTargetMod.korean-backup-$timestamp"
    Write-Host "Backing up retired Korean mod folder..."
    Copy-Item -LiteralPath $legacyTargetMod -Destination $legacyModBackup -Recurse -Force
    Remove-Item -LiteralPath $legacyTargetMod -Recurse -Force
}

Write-Host "Installing Korean translation data to OpenMW mods folder..."
Copy-Item -LiteralPath $payloadMod -Destination $targetMod -Recurse -Force

foreach ($requiredModFile in $requiredModFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $targetMod $requiredModFile) -PathType Leaf)) {
        throw "Korean translation file was not installed correctly: $requiredModFile"
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $targetMod "l10n") -PathType Container)) {
    throw "Korean translation l10n directory was not installed correctly: $targetMod"
}

Write-Host "Updating OpenMW user configuration..."
if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    & $configUpdater -OpenMWPath $OpenMWPath
} else {
    & $configUpdater -OpenMWPath $OpenMWPath -ConfigPath $ConfigPath
}

Write-Host ""
Write-Host "Korean OpenMW installation completed."
Write-Host "OpenMW       : $OpenMWPath"
Write-Host "Korean mod   : $targetMod"
Write-Host "Engine backup: $engineBackup"
if (-not [string]::IsNullOrWhiteSpace($modBackup)) {
    Write-Host "Mod backup   : $modBackup"
}
if (-not [string]::IsNullOrWhiteSpace($legacyModBackup)) {
    Write-Host "Legacy backup: $legacyModBackup"
}

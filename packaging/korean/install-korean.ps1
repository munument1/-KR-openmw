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
$configUpdater = Join-Path $scriptDir "install-korean-config.ps1"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if (-not (Test-Path -LiteralPath $payloadExe)) {
    throw "Korean openmw.exe payload not found: $payloadExe"
}
if (-not (Test-Path -LiteralPath $payloadFonts)) {
    throw "Korean font payload not found: $payloadFonts"
}
if (-not (Test-Path -LiteralPath $configUpdater)) {
    throw "Config updater not found: $configUpdater"
}

function Test-OpenMWInstall([string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try {
        $full = [System.IO.Path]::GetFullPath($Path)
        return (Test-Path -LiteralPath (Join-Path $full "openmw.exe"))
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
New-Item -ItemType Directory -Path $targetFonts -Force | Out-Null

$engineBackup = "$targetExe.korean-backup-$timestamp"
Copy-Item -LiteralPath $targetExe -Destination $engineBackup -Force

Write-Host "Installing Korean OpenMW engine..."
Copy-Item -LiteralPath $payloadExe -Destination $targetExe -Force

Write-Host "Installing Korean font assets..."
Get-ChildItem -LiteralPath $payloadFonts -File | ForEach-Object {
    $destination = Join-Path $targetFonts $_.Name
    if (Test-Path -LiteralPath $destination) {
        Copy-Item -LiteralPath $destination -Destination "$destination.korean-backup-$timestamp" -Force
    }
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
}

Write-Host "Updating OpenMW user configuration..."
if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    & $configUpdater
} else {
    & $configUpdater -ConfigPath $ConfigPath
}

Write-Host ""
Write-Host "Korean OpenMW installation completed."
Write-Host "OpenMW : $OpenMWPath"
Write-Host "Engine backup: $engineBackup"

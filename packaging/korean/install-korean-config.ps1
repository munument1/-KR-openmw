[CmdletBinding()]
param(
    [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"

$beginMarker = "# BEGIN OPENMW KOREAN MANAGED FALLBACKS"
$endMarker = "# END OPENMW KOREAN MANAGED FALLBACKS"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$payloadPath = Join-Path $scriptDir "korean-fallbacks.cfg"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if (-not (Test-Path -LiteralPath $payloadPath)) {
    throw "Korean fallback payload not found: $payloadPath"
}

if ([string]::IsNullOrWhiteSpace($ConfigPath)) {
    $documents = [Environment]::GetFolderPath('MyDocuments')
    $ConfigPath = Join-Path $documents "My Games\OpenMW\openmw.cfg"
}

$ConfigPath = [System.IO.Path]::GetFullPath($ConfigPath)
if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "OpenMW config not found: $ConfigPath`nRun OpenMW once first, or pass -ConfigPath <path>."
}

$payloadLines = [System.IO.File]::ReadAllLines($payloadPath, $utf8NoBom)
$managedKeys = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($line in $payloadLines) {
    if ($line -match '^\s*fallback=([^,]+),') {
        [void]$managedKeys.Add($Matches[1].Trim())
    }
}

if ($managedKeys.Count -eq 0) {
    throw "No managed fallback keys were found in $payloadPath"
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$ConfigPath.korean-backup-$timestamp"
Copy-Item -LiteralPath $ConfigPath -Destination $backupPath -Force

$currentLines = [System.IO.File]::ReadAllLines($ConfigPath, $utf8NoBom)
$outputLines = New-Object 'System.Collections.Generic.List[string]'
$insideManagedBlock = $false

foreach ($line in $currentLines) {
    if ($line.Trim() -eq $beginMarker) {
        if ($insideManagedBlock) {
            throw "Nested Korean managed block detected in $ConfigPath"
        }
        $insideManagedBlock = $true
        continue
    }

    if ($insideManagedBlock) {
        if ($line.Trim() -eq $endMarker) {
            $insideManagedBlock = $false
        }
        continue
    }

    if ($line -match '^\s*fallback=([^,]+),' -and $managedKeys.Contains($Matches[1].Trim())) {
        continue
    }

    [void]$outputLines.Add($line)
}

if ($insideManagedBlock) {
    throw "Unclosed Korean managed block detected in $ConfigPath. Backup created at $backupPath"
}

$managedBlock = New-Object 'System.Collections.Generic.List[string]'
[void]$managedBlock.Add($beginMarker)
foreach ($line in $payloadLines) {
    [void]$managedBlock.Add($line)
}
[void]$managedBlock.Add($endMarker)

$encodingIndex = -1
for ($i = $outputLines.Count - 1; $i -ge 0; $i--) {
    if ($outputLines[$i] -match '^\s*encoding\s*=') {
        $encodingIndex = $i
        break
    }
}

$finalLines = New-Object 'System.Collections.Generic.List[string]'
if ($encodingIndex -ge 0) {
    for ($i = 0; $i -lt $encodingIndex; $i++) {
        [void]$finalLines.Add($outputLines[$i])
    }

    while ($finalLines.Count -gt 0 -and [string]::IsNullOrWhiteSpace($finalLines[$finalLines.Count - 1])) {
        $finalLines.RemoveAt($finalLines.Count - 1)
    }
    if ($finalLines.Count -gt 0) {
        [void]$finalLines.Add("")
    }
    foreach ($line in $managedBlock) {
        [void]$finalLines.Add($line)
    }

    for ($i = $encodingIndex; $i -lt $outputLines.Count; $i++) {
        [void]$finalLines.Add($outputLines[$i])
    }
} else {
    while ($outputLines.Count -gt 0 -and [string]::IsNullOrWhiteSpace($outputLines[$outputLines.Count - 1])) {
        $outputLines.RemoveAt($outputLines.Count - 1)
    }
    foreach ($line in $outputLines) {
        [void]$finalLines.Add($line)
    }
    if ($finalLines.Count -gt 0) {
        [void]$finalLines.Add("")
    }
    foreach ($line in $managedBlock) {
        [void]$finalLines.Add($line)
    }
}

[System.IO.File]::WriteAllLines($ConfigPath, $finalLines, $utf8NoBom)

Write-Host "Updated OpenMW Korean fallback configuration."
Write-Host "Config : $ConfigPath"
Write-Host "Backup : $backupPath"
Write-Host "Managed fallback keys: $($managedKeys.Count)"
if ($encodingIndex -ge 0) {
    Write-Host "Managed block inserted immediately before the final encoding= line."
} else {
    Write-Host "Managed block appended at the end because no encoding= line exists."
}

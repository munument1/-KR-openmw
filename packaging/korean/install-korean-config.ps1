[CmdletBinding()]
param(
    [string]$ConfigPath = "",
    [string]$OpenMWPath = ""
)

$ErrorActionPreference = "Stop"

$fallbackBeginMarker = "# BEGIN OPENMW KOREAN MANAGED FALLBACKS"
$fallbackEndMarker = "# END OPENMW KOREAN MANAGED FALLBACKS"
$dataBeginMarker = "# BEGIN OPENMW KOREAN MANAGED DATA"
$dataEndMarker = "# END OPENMW KOREAN MANAGED DATA"
$contentBeginMarker = "# BEGIN OPENMW KOREAN MANAGED CONTENT"
$contentEndMarker = "# END OPENMW KOREAN MANAGED CONTENT"
$modFolderName = "Morrowind_Korean_ReTranslation_v01"
$pluginFileName = "Morrowind_Korean_ReTranslation_v01.esp"
$retiredPluginFileName = "Morrowind_Korean_Interior_CellNames_v01.esp"
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

$manageMod = -not [string]::IsNullOrWhiteSpace($OpenMWPath)
$dataLine = ""
if ($manageMod) {
    $OpenMWPath = [System.IO.Path]::GetFullPath($OpenMWPath)
    if (-not (Test-Path -LiteralPath (Join-Path $OpenMWPath "openmw.exe") -PathType Leaf)) {
        throw "OpenMW installation not found at: $OpenMWPath"
    }

    $modDataPath = Join-Path $OpenMWPath "mods\$modFolderName"
    if (-not (Test-Path -LiteralPath (Join-Path $modDataPath $pluginFileName) -PathType Leaf)) {
        throw "Korean translation ESP not found in OpenMW mods folder: $modDataPath"
    }
    $cfgModDataPath = $modDataPath.Replace('\', '/')
    $dataLine = 'data="' + $cfgModDataPath + '"'
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
$managedEndMarker = ""

foreach ($line in $currentLines) {
    $trimmed = $line.Trim()

    if (-not [string]::IsNullOrWhiteSpace($managedEndMarker)) {
        if ($trimmed -eq $managedEndMarker) {
            $managedEndMarker = ""
        }
        continue
    }

    if ($trimmed -eq $fallbackBeginMarker) {
        $managedEndMarker = $fallbackEndMarker
        continue
    }
    if ($trimmed -eq $dataBeginMarker) {
        $managedEndMarker = $dataEndMarker
        continue
    }
    if ($trimmed -eq $contentBeginMarker) {
        $managedEndMarker = $contentEndMarker
        continue
    }

    if ($line -match '^\s*fallback=([^,]+),' -and $managedKeys.Contains($Matches[1].Trim())) {
        continue
    }

    if ($manageMod) {
        if ($line -match '^\s*content\s*=\s*(.+?)\s*$') {
            $contentName = $Matches[1].Trim().Trim('"')
            if ($contentName -ieq $pluginFileName -or $contentName -ieq $retiredPluginFileName) {
                continue
            }
        }

        if ($line -match '^\s*data\s*=\s*(.*)$') {
            $dataValue = $Matches[1].Trim().Trim('"').Replace('\', '/')
            if ($dataValue.TrimEnd('/') -match ('(?i)(^|/)mods/' + [regex]::Escape($modFolderName) + '$')) {
                continue
            }
        }
    }

    [void]$outputLines.Add($line)
}

if (-not [string]::IsNullOrWhiteSpace($managedEndMarker)) {
    throw "Unclosed Korean managed block detected in $ConfigPath. Backup created at $backupPath"
}

function Insert-LinesAt {
    param(
        [System.Collections.Generic.List[string]]$List,
        [int]$Index,
        [string[]]$Lines
    )
    for ($j = $Lines.Count - 1; $j -ge 0; $j--) {
        $List.Insert($Index, $Lines[$j])
    }
}

if ($manageMod) {
    $dataBlock = @(
        $dataBeginMarker,
        $dataLine,
        $dataEndMarker
    )

    $lastDataIndex = -1
    for ($i = 0; $i -lt $outputLines.Count; $i++) {
        if ($outputLines[$i] -match '^\s*data\s*=') {
            $lastDataIndex = $i
        }
    }

    if ($lastDataIndex -ge 0) {
        Insert-LinesAt -List $outputLines -Index ($lastDataIndex + 1) -Lines $dataBlock
    } else {
        $firstContentIndex = -1
        for ($i = 0; $i -lt $outputLines.Count; $i++) {
            if ($outputLines[$i] -match '^\s*content\s*=') {
                $firstContentIndex = $i
                break
            }
        }
        if ($firstContentIndex -ge 0) {
            Insert-LinesAt -List $outputLines -Index $firstContentIndex -Lines $dataBlock
        } else {
            foreach ($line in $dataBlock) {
                [void]$outputLines.Add($line)
            }
        }
    }

    $contentBlock = @(
        $contentBeginMarker,
        "content=$pluginFileName",
        $contentEndMarker
    )

    $lastOfficialMasterIndex = -1
    for ($i = 0; $i -lt $outputLines.Count; $i++) {
        if ($outputLines[$i] -match '^\s*content\s*=\s*(Morrowind\.esm|Tribunal\.esm|Bloodmoon\.esm)\s*$') {
            $lastOfficialMasterIndex = $i
        }
    }

    if ($lastOfficialMasterIndex -ge 0) {
        Insert-LinesAt -List $outputLines -Index ($lastOfficialMasterIndex + 1) -Lines $contentBlock
    } else {
        $firstContentIndex = -1
        for ($i = 0; $i -lt $outputLines.Count; $i++) {
            if ($outputLines[$i] -match '^\s*content\s*=') {
                $firstContentIndex = $i
                break
            }
        }
        if ($firstContentIndex -ge 0) {
            Insert-LinesAt -List $outputLines -Index $firstContentIndex -Lines $contentBlock
        } else {
            foreach ($line in $contentBlock) {
                [void]$outputLines.Add($line)
            }
        }
    }
}

$fallbackBlock = New-Object 'System.Collections.Generic.List[string]'
[void]$fallbackBlock.Add($fallbackBeginMarker)
foreach ($line in $payloadLines) {
    [void]$fallbackBlock.Add($line)
}
[void]$fallbackBlock.Add($fallbackEndMarker)

$encodingIndex = -1
for ($i = $outputLines.Count - 1; $i -ge 0; $i--) {
    if ($outputLines[$i] -match '^\s*encoding\s*=') {
        $encodingIndex = $i
        break
    }
}

if ($encodingIndex -ge 0) {
    Insert-LinesAt -List $outputLines -Index $encodingIndex -Lines $fallbackBlock.ToArray()
} else {
    if ($outputLines.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace($outputLines[$outputLines.Count - 1])) {
        [void]$outputLines.Add("")
    }
    foreach ($line in $fallbackBlock) {
        [void]$outputLines.Add($line)
    }
}

[System.IO.File]::WriteAllLines($ConfigPath, $outputLines, $utf8NoBom)

Write-Host "Updated OpenMW Korean configuration."
Write-Host "Config : $ConfigPath"
Write-Host "Backup : $backupPath"
Write-Host "Managed fallback keys: $($managedKeys.Count)"
if ($manageMod) {
    Write-Host "Korean data : $dataLine"
    Write-Host "Korean plugin: content=$pluginFileName"
}
if ($encodingIndex -ge 0) {
    Write-Host "Managed fallback block inserted immediately before the final encoding= line."
} else {
    Write-Host "Managed fallback block appended at the end because no encoding= line exists."
}

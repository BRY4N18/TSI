#!/usr/bin/env pwsh
# Create a new feature
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$AllowExistingBranch,
    [switch]$DryRun,
    [string]$ShortName,
    [Parameter()]
    [long]$Number = 0,
    [switch]$Timestamp,
    [switch]$Layered,
    [switch]$Help,
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$FeatureDescription
)
$ErrorActionPreference = 'Stop'

# Show help if requested
if ($Help) {
    Write-Host "Usage: ./create-new-feature.ps1 [-Json] [-DryRun] [-AllowExistingBranch] [-ShortName <name>] [-Number N] [-Timestamp] [-Layered] <feature description>"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Json               Output in JSON format"
    Write-Host "  -DryRun             Compute feature name and paths without creating directories or files"
    Write-Host "  -AllowExistingBranch  Reuse an existing feature directory if it already exists"
    Write-Host "  -ShortName <name>   Provide a custom short name (2-4 words) for the feature"
    Write-Host "  -Number N           Specify branch number manually (overrides auto-detection)"
    Write-Host "  -Timestamp          Use timestamp prefix (YYYYMMDD-HHMMSS) instead of sequential numbering"
    Write-Host "  -Layered            Create {module}.md index + backend/ + frontend/ stubs (BE-first; feature.json -> backend; not README.md)"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  ./create-new-feature.ps1 'Add user authentication system' -ShortName 'user-auth'"
    Write-Host "  ./create-new-feature.ps1 -Layered -ShortName 'registro-accidente' 'Registro de accidentes'"
    exit 0
}

# Check if feature description provided
if (-not $FeatureDescription -or $FeatureDescription.Count -eq 0) {
    Write-Error "Usage: ./create-new-feature.ps1 [-Json] [-DryRun] [-AllowExistingBranch] [-ShortName <name>] [-Number N] [-Timestamp] <feature description>"
    exit 1
}

$featureDesc = ($FeatureDescription -join ' ').Trim()

# Validate description is not empty after trimming (e.g., user passed only whitespace)
if ([string]::IsNullOrWhiteSpace($featureDesc)) {
    Write-Error "Error: Feature description cannot be empty or contain only whitespace"
    exit 1
}

function Get-HighestNumberFromSpecs {
    param([string]$SpecsDir)

    [long]$highest = 0
    if (Test-Path $SpecsDir) {
        Get-ChildItem -Path $SpecsDir -Directory | ForEach-Object {
            # Match sequential prefixes (>=3 digits), but skip timestamp dirs.
            if ($_.Name -match '^(\d{3,})-' -and $_.Name -notmatch '^\d{8}-\d{6}-') {
                [long]$num = 0
                if ([long]::TryParse($matches[1], [ref]$num) -and $num -gt $highest) {
                    $highest = $num
                }
            }
        }
    }
    return $highest
}

function ConvertTo-CleanBranchName {
    param([string]$Name)

    return $Name.ToLower() -replace '[^a-z0-9]', '-' -replace '-{2,}', '-' -replace '^-', '' -replace '-$', ''
}
# Load common functions (includes Get-RepoRoot and Resolve-Template)
. "$PSScriptRoot/common.ps1"

# Use common.ps1 functions which prioritize .specify
$repoRoot = Get-RepoRoot

Set-Location $repoRoot

$specsDir = Join-Path $repoRoot 'specs'
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $specsDir -Force | Out-Null
}

# Function to generate branch name with stop word filtering and length filtering
function Get-BranchName {
    param([string]$Description)

    # Common stop words to filter out
    $stopWords = @(
        'i', 'a', 'an', 'the', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'with', 'from',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might', 'must', 'shall',
        'this', 'that', 'these', 'those', 'my', 'your', 'our', 'their',
        'want', 'need', 'add', 'get', 'set'
    )

    # Convert to lowercase and extract words (alphanumeric only)
    $cleanName = $Description.ToLower() -replace '[^a-z0-9\s]', ' '
    $words = $cleanName -split '\s+' | Where-Object { $_ }

    # Filter words: remove stop words and words shorter than 3 chars (unless they're uppercase acronyms in original)
    $meaningfulWords = @()
    foreach ($word in $words) {
        # Skip stop words
        if ($stopWords -contains $word) { continue }

        # Keep words that are length >= 3 OR appear as uppercase in original (likely acronyms)
        if ($word.Length -ge 3) {
            $meaningfulWords += $word
        } elseif ($Description -cmatch "\b$($word.ToUpper())\b") {
            # Keep short words only if they appear as uppercase in original (likely
            # acronyms). Use -cmatch so the comparison is case-sensitive, matching the
            # bash script's case-sensitive grep; -match would be case-insensitive and
            # would keep every short word.
            $meaningfulWords += $word
        }
    }

    # If we have meaningful words, use first 3-4 of them
    if ($meaningfulWords.Count -gt 0) {
        $maxWords = if ($meaningfulWords.Count -eq 4) { 4 } else { 3 }
        $result = ($meaningfulWords | Select-Object -First $maxWords) -join '-'
        return $result
    } else {
        # Fallback to original logic if no meaningful words found
        $result = ConvertTo-CleanBranchName -Name $Description
        $fallbackWords = ($result -split '-') | Where-Object { $_ } | Select-Object -First 3
        return [string]::Join('-', $fallbackWords)
    }
}

# Generate branch name
if ($ShortName) {
    # Use provided short name, just clean it up
    $branchSuffix = ConvertTo-CleanBranchName -Name $ShortName
} else {
    # Generate from description with smart filtering
    $branchSuffix = Get-BranchName -Description $featureDesc
}

# Warn if -Number and -Timestamp are both specified. Use ContainsKey (not
# `-ne 0`) so an explicit `-Number 0` is also detected, matching the bash twin's
# `[ -n "$BRANCH_NUMBER" ]` check.
if ($Timestamp -and $PSBoundParameters.ContainsKey('Number')) {
    Write-Warning "[specify] Warning: -Number is ignored when -Timestamp is used"
    $Number = 0
}

# Determine branch prefix
if ($Timestamp) {
    $featureNum = Get-Date -Format 'yyyyMMdd-HHmmss'
    $branchName = "$featureNum-$branchSuffix"
} else {
    # Determine branch number from existing feature directories. Auto-detect only
    # when -Number was not supplied; an explicit value (including 0) is honored,
    # matching the bash twin's `[ -z "$BRANCH_NUMBER" ]` check.
    if (-not $PSBoundParameters.ContainsKey('Number')) {
        $Number = (Get-HighestNumberFromSpecs -SpecsDir $specsDir) + 1
    }

    $featureNum = ('{0:000}' -f $Number)
    $branchName = "$featureNum-$branchSuffix"
}

# GitHub enforces a 244-byte limit on branch names
# Validate and truncate if necessary
$maxBranchLength = 244
if ($branchName.Length -gt $maxBranchLength) {
    # Calculate how much we need to trim from suffix
    # Account for prefix length: timestamp (15) + hyphen (1) = 16, or sequential (3) + hyphen (1) = 4
    $prefixLength = $featureNum.Length + 1
    $maxSuffixLength = $maxBranchLength - $prefixLength

    # Truncate suffix
    $truncatedSuffix = $branchSuffix.Substring(0, [Math]::Min($branchSuffix.Length, $maxSuffixLength))
    # Remove trailing hyphen if truncation created one
    $truncatedSuffix = $truncatedSuffix -replace '-$', ''

    $originalBranchName = $branchName
    $branchName = "$featureNum-$truncatedSuffix"

    Write-Warning "[specify] Branch name exceeded GitHub's 244-byte limit"
    Write-Warning "[specify] Original: $originalBranchName ($($originalBranchName.Length) bytes)"
    Write-Warning "[specify] Truncated to: $branchName ($($branchName.Length) bytes)"
}

$featureDir = Join-Path $specsDir $branchName
$specFile = Join-Path $featureDir 'spec.md'
$activeFeatureDir = $featureDir
$moduleShort = $null
$moduleIndexPath = $null

# Layered modules: Speckit feature dir is the active *layer* (backend first).
# Parent holds only `{module}.md` index (not README.md) + backend/ + frontend/.
if ($Layered) {
    $moduleShort = if ($ShortName) { ConvertTo-CleanBranchName $ShortName } else { ($branchName -replace '^\d+-', '') }
    $moduleIndexPath = Join-Path $featureDir "$moduleShort.md"
    $backendDir = Join-Path $featureDir 'backend'
    $activeFeatureDir = $backendDir
    $specFile = Join-Path $backendDir 'spec.md'
}

if (-not $DryRun) {
    if ((Test-Path -LiteralPath $featureDir -PathType Container) -and -not $AllowExistingBranch) {
        if ($Timestamp) {
            Write-Error "Error: Feature directory '$featureDir' already exists. Rerun to get a new timestamp or use a different -ShortName."
        } else {
            Write-Error "Error: Feature directory '$featureDir' already exists. Please use a different feature name or specify a different number with -Number."
        }
        exit 1
    }

    New-Item -ItemType Directory -Path $featureDir -Force | Out-Null

    if ($Layered) {
        $frontendDir = Join-Path $featureDir 'frontend'
        New-Item -ItemType Directory -Path $backendDir -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $backendDir 'contracts') -Force | Out-Null
        New-Item -ItemType Directory -Path $frontendDir -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $frontendDir 'contracts') -Force | Out-Null

        $indexBody = @"
# Módulo: $moduleShort

**Ubicación:** ``specs/.../$branchName/``

Índice global del módulo (no es una spec Speckit). Feature activa = capa en ``.specify/feature.json``.

## Capas

| Capa | Ruta | Autoridad |
|------|------|-----------|
| Backend | [``backend/``](./backend/) | Dominio, API, OpenAPI (primero) |
| Frontend | [``frontend/``](./frontend/) | Interaction Capability (después; Depends-on backend) |

## Orden

1. Trabajar ``backend/`` (``feature.json`` → ``.../backend``).
2. Luego ``frontend/`` con Depends-on ``../backend`` — sin redefinir RF/RN de dominio.

## Convención de nombres

El índice se llama **igual que la carpeta del módulo** (``$moduleShort.md``), no ``README.md``.
"@
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($moduleIndexPath, $indexBody, $utf8NoBom)

        $beTemplate = Resolve-Template -TemplateName 'spec-template' -RepoRoot $repoRoot
        if ($beTemplate -and (Test-Path $beTemplate)) {
            $content = [System.IO.File]::ReadAllText($beTemplate)
            [System.IO.File]::WriteAllText($specFile, $content, $utf8NoBom)
        } else {
            [Console]::Error.WriteLine("Warning: Spec template not found; created empty backend spec")
            New-Item -ItemType File -Path $specFile -Force | Out-Null
        }

        $feSpec = Join-Path $frontendDir 'spec.md'
        $feTemplate = Resolve-Template -TemplateName 'spec-template-frontend' -RepoRoot $repoRoot
        if ($feTemplate -and (Test-Path $feTemplate)) {
            $feContent = [System.IO.File]::ReadAllText($feTemplate)
            [System.IO.File]::WriteAllText($feSpec, $feContent, $utf8NoBom)
        } else {
            $feStub = @"
# Feature Specification: [FEATURE] — Frontend

**Depends-on**: ``../backend/spec.md``

**Status**: Draft (crear después del backend)

## Functional Requirements (UI)

- **FR-UI-001**: [describir interacción]

## Out of Scope

- Redefinir RF/RN/API del backend
"@
            [System.IO.File]::WriteAllText($feSpec, $feStub, $utf8NoBom)
        }
    }
    else {
        if (-not (Test-Path -PathType Leaf $specFile)) {
            $template = Resolve-Template -TemplateName 'spec-template' -RepoRoot $repoRoot
            if ($template -and (Test-Path $template)) {
                $content = [System.IO.File]::ReadAllText($template)
                $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
                [System.IO.File]::WriteAllText($specFile, $content, $utf8NoBom)
            } else {
                [Console]::Error.WriteLine("Warning: Spec template not found; created empty spec file")
                New-Item -ItemType File -Path $specFile -Force | Out-Null
            }
        }
    }

    # Persist to .specify/feature.json so downstream commands can find the feature
    Save-FeatureJson -RepoRoot $repoRoot -FeatureDirectory $activeFeatureDir

    # Set environment variables for the current session
    $env:SPECIFY_FEATURE = $branchName
    $env:SPECIFY_FEATURE_DIRECTORY = $activeFeatureDir
}

if ($Json) {
    $obj = [PSCustomObject]@{
        BRANCH_NAME = $branchName
        SPEC_FILE = $specFile
        FEATURE_NUM = $featureNum
        FEATURE_DIR = $activeFeatureDir
        LAYERED = [bool]$Layered
    }
    if ($Layered -and $moduleIndexPath) {
        $obj | Add-Member -NotePropertyName 'MODULE_INDEX' -NotePropertyValue $moduleIndexPath
        $obj | Add-Member -NotePropertyName 'MODULE_ROOT' -NotePropertyValue $featureDir
    }
    if ($DryRun) {
        $obj | Add-Member -NotePropertyName 'DRY_RUN' -NotePropertyValue $true
    }
    $obj | ConvertTo-Json -Compress
} else {
    Write-Output "BRANCH_NAME: $branchName"
    Write-Output "SPEC_FILE: $specFile"
    Write-Output "FEATURE_NUM: $featureNum"
    if ($Layered) {
        Write-Output "LAYERED: backend+frontend (active=backend)"
        Write-Output "MODULE_ROOT: $featureDir"
        Write-Output "MODULE_INDEX: $moduleIndexPath"
    }
    if (-not $DryRun) {
        Write-Output "SPECIFY_FEATURE set to: $branchName"
        Write-Output "SPECIFY_FEATURE_DIRECTORY set to: $activeFeatureDir"
    }
}

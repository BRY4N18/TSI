<#
.SYNOPSIS
  Speckit prerequisites check for the active feature (from .specify/feature.json).

.DESCRIPTION
  Emits JSON with FEATURE_DIR and AVAILABLE_DOCS for Speckit analyze/implement.
  Usage: .\.specify\scripts\powershell\check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
#>
[CmdletBinding()]
param(
  [switch]$Json,
  [switch]$RequireTasks,
  [switch]$IncludeTasks
)

$ErrorActionPreference = 'Stop'
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')

$featureJsonPath = Join-Path $repoRoot '.specify\feature.json'
if (-not (Test-Path $featureJsonPath)) {
  Write-Error "Missing .specify/feature.json. Run /speckit-specify first."
  exit 1
}

$featureMeta = Get-Content -Raw -Path $featureJsonPath | ConvertFrom-Json
$relFeatureDir = $featureMeta.feature_directory
if ([string]::IsNullOrWhiteSpace($relFeatureDir)) {
  Write-Error "feature.json missing feature_directory."
  exit 1
}

$featureDir = Join-Path $repoRoot ($relFeatureDir -replace '/', '\')

if (-not (Test-Path (Join-Path $featureDir 'spec.md'))) {
  Write-Error "Missing FEATURE_DIR/spec.md at $featureDir. Run /speckit-specify first."
  exit 1
}
if (-not (Test-Path (Join-Path $featureDir 'plan.md'))) {
  Write-Error "Missing FEATURE_DIR/plan.md at $featureDir. Run /speckit-plan first."
  exit 1
}
if ($RequireTasks -and -not (Test-Path (Join-Path $featureDir 'tasks.md'))) {
  Write-Error "Missing FEATURE_DIR/tasks.md at $featureDir. Run /speckit-tasks first."
  exit 1
}

$docs = @('spec.md', 'plan.md')
foreach ($name in @(
  'data-model.md',
  'research.md',
  'quickstart.md',
  'traceability.md'
)) {
  if (Test-Path (Join-Path $featureDir $name)) {
    $docs += $name
  }
}

$contractsDir = Join-Path $featureDir 'contracts'
if (Test-Path $contractsDir) {
  Get-ChildItem -Path $contractsDir -Filter '*.yaml' -File -ErrorAction SilentlyContinue |
    ForEach-Object { $docs += ("contracts/" + $_.Name) }
  Get-ChildItem -Path $contractsDir -Filter '*.yml' -File -ErrorAction SilentlyContinue |
    ForEach-Object { $docs += ("contracts/" + $_.Name) }
}

if ($IncludeTasks -and (Test-Path (Join-Path $featureDir 'tasks.md'))) {
  $docs += 'tasks.md'
}

if ($Json) {
  $payload = [ordered]@{
    FEATURE_DIR     = $featureDir
    AVAILABLE_DOCS  = $docs
    HAS_TASKS       = [bool](Test-Path (Join-Path $featureDir 'tasks.md'))
    HAS_CHECKLISTS  = [bool](Test-Path (Join-Path $featureDir 'checklists'))
  }
  $payload | ConvertTo-Json -Compress
  exit 0
}

Write-Host "FEATURE_DIR=$featureDir"
Write-Host ("AVAILABLE_DOCS=" + ($docs -join ','))

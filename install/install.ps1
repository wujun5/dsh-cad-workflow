# install.ps1 - install skills and rendered MCP bundles into DSH.
# Run configure.ps1 FIRST so _rendered/bundles contains your machine paths.
# Skills are plain files copied to DSH_HOME/skills (backed up to .bak).
# Bundles MUST be registered via `dsh plugin --profile <p> add <dir>` so pnpm
# creates the link: dependency + Junction; plain file copy is NOT enough.
# Pure ASCII on purpose (PowerShell 5.1 default GBK mangles Chinese here-strings).

param(
  [string]$EnvFile = (Join-Path $PSScriptRoot '..\my-env.json'),
  [string]$Root    = (Join-Path $PSScriptRoot '..')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $EnvFile)) {
  Write-Host "[install] No my-env.json found. Copy my-env.example.json -> my-env.json first."
  exit 2
}
$cfg = Get-Content -LiteralPath $EnvFile -Raw -Encoding UTF8 | ConvertFrom-Json

$dshHome = [string]$cfg.dsh_home
$profile = [string]$cfg.dsh_profile
if (-not $dshHome -or -not $profile) {
  Write-Host "[install] my-env.json must define dsh_home and dsh_profile."
  exit 2
}

# ---- 1. skills: plain files, backup + copy ----
$skillsSrc = Join-Path $Root 'skills'
$skillsDst = Join-Path $dshHome 'skills'
Write-Host "[install] Skills -> $skillsDst"
foreach ($s in @('cad-spec-driver','cad-confirm-gate','cad-blender-ops','cad-freecad-ops','cad-verify')) {
  $src = Join-Path $skillsSrc "$s\SKILL.md"
  $dst = Join-Path $skillsDst "$s\SKILL.md"
  if (-not (Test-Path -LiteralPath $src)) { Write-Host "[install]   MISSING skill source: $src"; continue }
  New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
  if (Test-Path -LiteralPath $dst) { Copy-Item -LiteralPath $dst -Destination "$dst.bak" -Force }
  Copy-Item -LiteralPath $src -Destination $dst -Force
  Write-Host "[install]   skill $s OK"
}

# ---- 2. bundles: register via dsh CLI (pnpm link) ----
$rendered = Join-Path $Root '_rendered\bundles'
if (-not (Test-Path -LiteralPath $rendered)) {
  Write-Host "[install] No rendered bundles. Run configure.ps1 first."
  exit 2
}
$dshCmd = (Get-Command dsh -ErrorAction SilentlyContinue).Source
if (-not $dshCmd) {
  Write-Host "[install] 'dsh' CLI not on PATH. Bundles not installed."
  Write-Host "[install] Add DSH's runtime/cli/bin to PATH, or install via the"
  Write-Host "[install] DSH GUI > Plugins > Install Bundle, selecting each rendered dir."
  exit 3
}

foreach ($b in @('blender-mcp','freecad-mcp')) {
  $dir = Join-Path $rendered $b
  if (-not (Test-Path -LiteralPath $dir)) { Write-Host "[install]   MISSING rendered bundle: $dir"; continue }
  Write-Host "[install]   bundle $b via dsh plugin add ..."
  & $dshCmd plugin --profile $profile add $dir 2>&1 | ForEach-Object { Write-Host "      $_" }
  if ($LASTEXITCODE -ne 0) { Write-Host "[install]   WARNING: pnpm add returned $LASTEXITCODE for $b" }
}

Write-Host "[install] Done. FULLY QUIT and restart DSH so skills/bundles reload."
Write-Host "[install] Then in Blender/FreeCAD GUI start their servers if you need MCP realtime."
Write-Host "[install] FreeCAD headless MCP needs no GUI."

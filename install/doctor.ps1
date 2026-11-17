# doctor.ps1 - health check: verify skills/bundles installed and paths reachable.
# Pure ASCII on purpose (PowerShell 5.1 default GBK mangles Chinese here-strings).

param(
  [string]$EnvFile = (Join-Path $PSScriptRoot '..\my-env.json'),
  [string]$Root    = (Join-Path $PSScriptRoot '..')
)

$ErrorActionPreference = 'Continue'
if (Test-Path -LiteralPath $EnvFile) {
  $cfg = Get-Content -LiteralPath $EnvFile -Raw -Encoding UTF8 | ConvertFrom-Json
} else {
  Write-Host "[doctor] No my-env.json; checking source tree only."
  $cfg = $null
}

function Check-Path($label, $path, $wantFile) {
  if (Test-Path -LiteralPath $path) {
    if ($wantFile) { Write-Host "  [OK]   $label : $path" }
    else { Write-Host "  [OK]   $label : $path" }
  } else {
    Write-Host "  [MISS] $label : $path"
  }
}

Write-Host "=== Source tree ==="
foreach ($s in @('cad-spec-driver','cad-confirm-gate','cad-blender-ops','cad-freecad-ops','cad-verify')) {
  Check-Path "skill/$s" (Join-Path $Root "skills\$s\SKILL.md") $true
}
foreach ($b in @('blender-mcp','freecad-mcp')) {
  Check-Path "bundle/$b" (Join-Path $Root "bundles\$b\cordis.patch.yml") $true
}

if ($cfg) {
  Write-Host "=== Machine paths (from my-env.json) ==="
  Check-Path 'uvx' ([string]$cfg.uvx) $true
  Check-Path 'FreeCADCmd' ([string]$cfg.freecadcmd) $true
  Check-Path 'DSH skills dir' ([string]$cfg.dsh_home + '\skills') $false
  $local = [string]$cfg.dsh_home + "\profiles\" + [string]$cfg.dsh_profile + "\node_modules\@local"
  Check-Path 'DSH @local bundles' $local $false
  foreach ($s in @('cad-spec-driver','cad-confirm-gate','cad-blender-ops','cad-freecad-ops','cad-verify')) {
    Check-Path "installed skill/$s" (Join-Path ([string]$cfg.dsh_home + '\skills') "$s\SKILL.md") $true
  }
  $bundleTargets = @{ 'blender-mcp' = 'blender-mcp-bridge'; 'freecad-mcp' = 'freecad-mcp-bridge' }
  foreach ($b in @('blender-mcp','freecad-mcp')) {
    Check-Path "installed bundle/$b" (Join-Path $local "$($bundleTargets[$b])\cordis.patch.yml") $true
  }
  $rendered = Join-Path $Root '_rendered\bundles'
  Check-Path 'rendered bundles' $rendered $false
}

Write-Host "=== Python deps (trimesh for verify_stl.py) ==="
$py = Get-Command python -ErrorAction SilentlyContinue
if ($py) {
  & python -c "import trimesh; print('  [OK]   trimesh', trimesh.__version__)" 2>&1
} else {
  Write-Host "  [MISS] python not on PATH"
}
Write-Host "[doctor] Done."

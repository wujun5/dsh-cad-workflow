# configure.ps1 - render bundle templates with machine-specific paths.
# Reads my-env.json (copy from my-env.example.json) and writes _rendered/bundles/
# with all __PLACEHOLDER__ tokens replaced. Run this before install.ps1.
# Pure ASCII on purpose (PowerShell 5.1 default GBK mangles Chinese here-strings).

param(
  [string]$EnvFile = (Join-Path $PSScriptRoot '..\my-env.json'),
  [string]$Root    = (Join-Path $PSScriptRoot '..')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $EnvFile)) {
  Write-Host "[configure] No my-env.json found at $EnvFile"
  Write-Host "[configure] Copy my-env.example.json -> my-env.json and fill in YOUR paths, then re-run."
  exit 2
}

$cfg = Get-Content -LiteralPath $EnvFile -Raw -Encoding UTF8 | ConvertFrom-Json
$rendered = Join-Path $Root '_rendered\bundles'
New-Item -ItemType Directory -Force -Path $rendered | Out-Null

$map = @{
  '__UVX__'          = [string]$cfg.uvx
  '__FREECADCMD__'   = [string]$cfg.freecadcmd
  '__BLENDER_HOST__' = [string]$cfg.blender_host
  '__BLENDER_PORT__' = [string]$cfg.blender_port
  '__FREECAD_HOST__' = [string]$cfg.freecad_host
}

foreach ($name in @('blender-mcp','freecad-mcp')) {
  $srcBundle = Join-Path $Root "bundles\$name"
  $dstBundle = Join-Path $rendered $name
  if (Test-Path -LiteralPath $dstBundle) { Remove-Item -LiteralPath $dstBundle -Recurse -Force }
  Copy-Item -LiteralPath $srcBundle -Destination $dstBundle -Recurse -Force

  $patch = Join-Path $dstBundle 'cordis.patch.yml'
  $text = Get-Content -LiteralPath $patch -Raw -Encoding UTF8
  foreach ($k in $map.Keys) {
    if ($null -eq $map[$k]) { continue }
    $text = $text.Replace($k, [string]$map[$k])
  }
  [System.IO.File]::WriteAllText($patch, $text, (New-Object System.Text.UTF8Encoding($false)))
  Write-Host "[configure] rendered $name"
}

Write-Host "[configure] Done. Rendered bundles in: $rendered"
Write-Host "[configure] Next: run install.ps1"

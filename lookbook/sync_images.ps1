# Copies the latest renders into lookbook\img so index.html shows them.
$root = Split-Path $PSScriptRoot -Parent
$img = Join-Path $PSScriptRoot "img"
New-Item -ItemType Directory -Force $img | Out-Null
Get-ChildItem (Join-Path $root "renders\sales\*.jpg") | Where-Object { $_.Name -notlike "quick_*" } | Copy-Item -Destination $img -Force
foreach ($f in "renders\10_cutaway.png", "renders\07_exposed_frame.png", "renders\09_exploded.png", "drawings\DRW_A_front_elevation.png") {
    Copy-Item (Join-Path $root $f) $img -Force
}
Write-Host "Lookbook images updated:" (Get-ChildItem $img).Count

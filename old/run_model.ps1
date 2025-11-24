# run_model.ps1 — lance le modèle avec les variables Qt fixées
$env:QT_ENABLE_HIGHDPI_SCALING = "0"
$env:QT_AUTO_SCREEN_SCALE_FACTOR = "0"
$env:QT_SCALE_FACTOR = "1"

# Appeler le python du venv explicitement
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $py python/model.py
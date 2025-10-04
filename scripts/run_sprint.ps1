
param([string]$Goal = "FastAPI'ye JWT auth ekle", [switch]$Auto)
$env:PYTHONPATH = (Get-Location).Path
$autoFlag = ""
if ($Auto) { $autoFlag = "--auto" }
python main.py "$Goal" $autoFlag

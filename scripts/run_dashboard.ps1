
param([string]$Workdir = "./workdir")
$env:PYTHONPATH = (Get-Location).Path
streamlit run dashboard/streamlit_app.py

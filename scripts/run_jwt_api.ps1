
$env:PYTHONPATH = (Get-Location).Path
uvicorn jwt_fastapi_app.app:app --reload --port 8000

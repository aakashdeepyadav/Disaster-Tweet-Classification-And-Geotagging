# PowerShell script to start the Flask server
Write-Host "Activating virtual environment..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

Write-Host "Starting Flask server..." -ForegroundColor Green
python app.py







# Start Backend Server for AiVideoForge
Write-Host "🚀 Starting AiVideoForge Backend..." -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit backend\.env and add your GOOGLE_API_KEY, then run this script again." -ForegroundColor Red
    Start-Process notepad ".env"
    Read-Host "Press Enter after you've saved your API key in .env"
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating Python virtual environment..." -ForegroundColor Green
    python -m venv venv
}

# Activate venv
Write-Host "📦 Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📦 Installing dependencies (first run may take a moment)..." -ForegroundColor Green
pip install -r requirements.txt --quiet

# Check for gTTS (free fallback for TTS)
pip install gtts --quiet

Write-Host ""
Write-Host "✅ Backend starting at http://localhost:8000" -ForegroundColor Green
Write-Host "📖 API Docs available at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

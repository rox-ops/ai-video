# Start Frontend for AiVideoForge
Write-Host "🌐 Starting AiVideoForge Frontend..." -ForegroundColor Cyan
Write-Host ""

$frontendDir = Split-Path -Parent $PSCommandPath | Split-Path -Parent
$frontendDir = Join-Path $frontendDir "frontend"

# Check if Python is available to serve files
$pythonAvailable = Get-Command python -ErrorAction SilentlyContinue
if ($pythonAvailable) {
    Write-Host "✅ Frontend serving at http://localhost:3000" -ForegroundColor Green
    Write-Host "📖 Open http://localhost:3000 in your browser" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
    Set-Location $frontendDir
    python -m http.server 3000
} else {
    # Fallback: just open the HTML file directly
    Write-Host "ℹ️  Opening frontend directly in browser..." -ForegroundColor Yellow
    $indexPath = Join-Path $frontendDir "index.html"
    Start-Process $indexPath
    Write-Host "Note: For full functionality, the backend must also be running." -ForegroundColor Yellow
}

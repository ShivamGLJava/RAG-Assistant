Write-Host ""
Write-Host "==================================="
Write-Host "Starting RAG Assistant"
Write-Host "==================================="

Write-Host ""
Write-Host "Cleaning stale Qdrant lock files..."

$lockFiles = @(
    "qdrant_data\.lock",
    "app\services\qdrant_data\.lock"
)

foreach ($lock in $lockFiles)
{
    if (Test-Path $lock)
    {
        Remove-Item $lock -Force
        Write-Host "Removed $lock"
    }
}

Write-Host ""
Write-Host "Starting FastAPI..."
Write-Host ""

uvicorn app.main:app --reload
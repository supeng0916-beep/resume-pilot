param(
    [int]$Port = 8501
)

$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $connections) {
    Write-Host "No process is listening on port $Port."
    exit 0
}

$process_ids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($process_id in $process_ids) {
    $process = Get-Process -Id $process_id -ErrorAction SilentlyContinue
    if ($process) {
        Stop-Process -Id $process_id -Force
        Write-Host "Stopped PID $process_id on port $Port."
    }
}

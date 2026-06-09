param(
    [int[]]$Ports = @(8000, 5173)
)

$ErrorActionPreference = "Stop"

foreach ($Port in $Ports) {
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if (-not $connections) {
        Write-Host "No process is listening on port $Port."
        continue
    }

    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $processId -Force
            Write-Host "Stopped PID $processId on port $Port."
        }
    }
}

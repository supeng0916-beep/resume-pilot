param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = "D:\python\python.exe"
$LogDir = Join-Path $ProjectRoot "data\test_outputs"
$OutLog = Join-Path $LogDir "streamlit_control_cabin.out.log"
$ErrLog = Join-Path $LogDir "streamlit_control_cabin.err.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$existing = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existing) {
    Write-Host "Control cabin is already listening on http://127.0.0.1:$Port"
    Write-Host "PID: $($existing.OwningProcess)"
    exit 0
}

$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
$env:PYTHONIOENCODING = "utf-8"

$arguments = @(
    "-m", "streamlit", "run", "app\streamlit_app.py",
    "--server.port", "$Port",
    "--server.address", "127.0.0.1",
    "--server.headless", "true",
    "--browser.gatherUsageStats", "false"
)

$process = Start-Process `
    -FilePath $Python `
    -ArgumentList $arguments `
    -WorkingDirectory $ProjectRoot `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog `
    -WindowStyle Hidden `
    -PassThru

Start-Sleep -Seconds 3

$started = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
if ($started) {
    Write-Host "Control cabin started: http://127.0.0.1:$Port"
    Write-Host "PID: $($started.OwningProcess)"
    Write-Host "Logs: $OutLog"
    exit 0
}

Write-Warning "Streamlit process was started but port $Port is not listening yet."
Write-Warning "Process ID: $($process.Id)"
Write-Warning "Check logs:"
Write-Warning $OutLog
Write-Warning $ErrLog
exit 1

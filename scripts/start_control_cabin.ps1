param(
    [int]$ApiPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Python = "D:\python\python.exe"
$LogDir = Join-Path $ProjectRoot "data\test_outputs"
$ApiOutLog = Join-Path $LogDir "fastapi_control_cabin.out.log"
$ApiErrLog = Join-Path $LogDir "fastapi_control_cabin.err.log"
$FrontendOutLog = Join-Path $LogDir "react_control_cabin.out.log"
$FrontendErrLog = Join-Path $LogDir "react_control_cabin.err.log"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-PortListening {
    param([int]$Port)
    return [bool](Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1)
}

function Stop-PortProcess {
    param([int]$Port)
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Stop-Process -Id $processId -Force
            Write-Host "Stopped stale PID $processId on port $Port."
        }
    }
}

function Test-ApiPrefixHealthy {
    param([int]$Port)
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/api/health" -UseBasicParsing -TimeoutSec 3
        $contentType = [string]$response.Headers["Content-Type"]
        return $response.StatusCode -eq 200 -and $contentType.StartsWith("application/json")
    }
    catch {
        return $false
    }
}

if ((Test-PortListening -Port $ApiPort) -and -not (Test-ApiPrefixHealthy -Port $ApiPort)) {
    Write-Host "Existing FastAPI process does not serve /api/health as JSON. Restarting it."
    Stop-PortProcess -Port $ApiPort
    Start-Sleep -Seconds 1
}

if (-not (Test-PortListening -Port $ApiPort)) {
    Start-Process `
        -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "api.server:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
        -WorkingDirectory $ProjectRoot `
        -RedirectStandardOutput $ApiOutLog `
        -RedirectStandardError $ApiErrLog `
        -WindowStyle Hidden `
        -PassThru | Out-Null
}

$FrontendRoot = Join-Path $ProjectRoot "frontend"
if (-not (Test-Path (Join-Path $FrontendRoot "node_modules"))) {
    Push-Location $FrontendRoot
    try {
        npm install
    }
    finally {
        Pop-Location
    }
}

if (-not (Test-PortListening -Port $FrontendPort)) {
    Start-Process `
        -FilePath "npm" `
        -ArgumentList @("run", "dev", "--", "--host", "127.0.0.1", "--port", "$FrontendPort") `
        -WorkingDirectory $FrontendRoot `
        -RedirectStandardOutput $FrontendOutLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru | Out-Null
}

Start-Sleep -Seconds 3

if ((Test-PortListening -Port $ApiPort) -and (Test-PortListening -Port $FrontendPort)) {
    Write-Host "React control cabin started: http://127.0.0.1:$FrontendPort"
    Write-Host "FastAPI started: http://127.0.0.1:$ApiPort"
    Write-Host "Logs: $LogDir"
    exit 0
}

Write-Warning "Control cabin did not finish starting."
Write-Warning "FastAPI logs: $ApiOutLog / $ApiErrLog"
Write-Warning "React logs: $FrontendOutLog / $FrontendErrLog"
exit 1

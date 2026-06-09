$ErrorActionPreference = "Stop"

Push-Location frontend
try {
    if (-not (Test-Path "node_modules")) {
        npm install
    }
    npm run dev
}
finally {
    Pop-Location
}

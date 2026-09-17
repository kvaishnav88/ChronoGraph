# ChronoGraph -- local dev preflight check.
Write-Host "ChronoGraph setup check" -ForegroundColor Cyan
Write-Host "------------------------"

$failed = $false

function Check-Pass($msg) { Write-Host "  [OK]   $msg" -ForegroundColor Green }
function Check-Fail($msg) { Write-Host "  [FAIL] $msg" -ForegroundColor Red; $script:failed = $true }
function Check-Warn($msg) { Write-Host "  [WARN] $msg" -ForegroundColor Yellow }

try {
    $pyVersion = (python --version) 2>&1
    if ($pyVersion -match "3\.1[1-3]\.") {
        Check-Pass "Python: $pyVersion"
    } else {
        Check-Fail "Python found ($pyVersion) but not 3.11-3.13 -- use 3.11.x."
    }
} catch {
    Check-Fail "Python not found on PATH."
}

try {
    $nodeVersion = node -v
    Check-Pass "Node: $nodeVersion"
} catch {
    Check-Fail "Node.js not found on PATH."
}

if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Check-Pass "venv exists at .\venv"
    if ($env:VIRTUAL_ENV) {
        Check-Pass "venv is currently ACTIVE"
    } else {
        Check-Warn "venv exists but not active. Run: .\venv\Scripts\Activate.ps1"
    }
} else {
    Check-Fail "No venv found. Run: python -m venv venv"
}

if (Test-Path ".\.env") {
    $envContent = Get-Content ".\.env" -Raw
    $required = @("GROQ_API_KEY", "NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE")
    foreach ($key in $required) {
        if ($envContent -match "$key\s*=\s*\S+") {
            Check-Pass ".env has $key"
        } else {
            Check-Fail ".env is missing or has an empty value for $key"
        }
    }
} else {
    Check-Fail ".env not found."
}

$neo4jUp = Test-NetConnection -ComputerName "localhost" -Port 7687 -WarningAction SilentlyContinue
if ($neo4jUp.TcpTestSucceeded) {
    Check-Pass "Neo4j is reachable on localhost:7687"
} else {
    Check-Fail "Neo4j is NOT reachable. Open Neo4j Desktop and click Start."
}

if (Test-Path ".\frontend\node_modules") {
    Check-Pass "frontend\node_modules exists"
} else {
    Check-Warn "frontend\node_modules missing. Run: cd frontend; npm install"
}

Write-Host "------------------------"
if ($failed) {
    Write-Host "Preflight FAILED -- fix the [FAIL] items above." -ForegroundColor Red
} else {
    Write-Host "Preflight passed. Run:" -ForegroundColor Green
    Write-Host "  Terminal 1: uvicorn api.main:app --reload --port 8000"
    Write-Host "  Terminal 2: cd frontend; npm run dev"
}
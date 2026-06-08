# ============================================================================
# RAG Assistant - Windows PowerShell Environment Bootstrap
# ============================================================================
#
# Purpose: Cross-platform environment automation for consistent developer setups
#
# Features:
#   - Virtual environment detection and creation
#   - pip dependency installation and upgrade
#   - Environment configuration templating
#   - Git ignore verification and protection
#   - Comprehensive logging and error handling
#
# Usage: .\setup.ps1
# ============================================================================

param(
    [switch]$Force = $false,
    [switch]$Verbose = $false
)

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

$ErrorActionPreference = "Continue"
$VerbosePreference = if ($Verbose) { "Continue" } else { "SilentlyContinue" }

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$VENV_DIR = Join-Path $PROJECT_ROOT ".venv"
$REQUIREMENTS_FILE = Join-Path $PROJECT_ROOT "requirements.txt"
$ENV_EXAMPLE_FILE = Join-Path $PROJECT_ROOT ".env.example"
$ENV_FILE = Join-Path $PROJECT_ROOT ".env"
$GITIGNORE_FILE = Join-Path $PROJECT_ROOT ".gitignore"

$PYTHON_VERSION_REQUIRED = "3.11"
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

# ============================================================================
# SYSTEM VALIDATION
# ============================================================================

function Test-SystemRequirements {
    Write-Header "Validating System Requirements"

    # Check Python installation
    try {
        $PythonVersion = python --version 2>&1
        Write-Info "Detected: $PythonVersion"
        Write-Success "Python is installed"
    }
    catch {
        Write-Error-Custom "Python not found. Please install Python 3.11+ from https://www.python.org/"
        exit 1
    }

    # Check Git installation
    try {
        $GitVersion = git --version 2>&1
        Write-Info "Detected: $GitVersion"
        Write-Success "Git is installed"
    }
    catch {
        Write-Error-Custom "Git not found. Please install Git from https://git-scm.com/"
        exit 1
    }

    # Verify project structure
    if (-not (Test-Path $REQUIREMENTS_FILE)) {
        Write-Error-Custom "requirements.txt not found at $REQUIREMENTS_FILE"
        exit 1
    }
    Write-Success "Project structure verified"
}

# ============================================================================
# VIRTUAL ENVIRONMENT MANAGEMENT
# ============================================================================

function Test-VirtualEnvironment {
    Write-Header "Checking Virtual Environment"

    if (Test-Path $VENV_DIR) {
        Write-Info "Virtual environment exists at $VENV_DIR"

        # Test if venv is functional
        $PythonExe = Join-Path $VENV_DIR "Scripts" "python.exe"
        if (Test-Path $PythonExe) {
            Write-Success "Virtual environment is valid and ready"
            return $true
        }
        else {
            Write-Warning "Virtual environment exists but appears corrupted"
            if ($Force) {
                Write-Info "Force flag set. Removing corrupted venv..."
                Remove-Item -Path $VENV_DIR -Recurse -Force
                return $false
            }
            else {
                Write-Warning "Run with -Force to recreate. Exiting."
                exit 1
            }
        }
    }
    else {
        Write-Info "No virtual environment found"
        return $false
    }
}

function New-VirtualEnvironment {
    Write-Header "Creating Virtual Environment"

    Write-Info "Running: python -m venv $VENV_DIR"
    try {
        python -m venv $VENV_DIR
        Write-Success "Virtual environment created successfully"
    }
    catch {
        Write-Error-Custom "Failed to create virtual environment: $_"
        exit 1
    }
}

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================

function Update-PipPackage {
    Write-Header "Upgrading pip Package Manager"

    $PythonExe = Join-Path $VENV_DIR "Scripts" "python.exe"
    $PipExe = Join-Path $VENV_DIR "Scripts" "pip.exe"

    if (-not (Test-Path $PipExe)) {
        Write-Error-Custom "pip executable not found. Virtual environment may be corrupted."
        exit 1
    }

    Write-Info "Upgrading pip to latest version..."
    try {
        & $PythonExe -m pip install --upgrade pip
        Write-Success "pip upgraded successfully"
    }
    catch {
        Write-Error-Custom "Failed to upgrade pip: $_"
        exit 1
    }
}

function Install-Dependencies {
    Write-Header "Installing Project Dependencies"

    $PipExe = Join-Path $VENV_DIR "Scripts" "pip.exe"

    if (-not (Test-Path $REQUIREMENTS_FILE)) {
        Write-Error-Custom "requirements.txt not found"
        exit 1
    }

    Write-Info "Installing packages from requirements.txt..."
    try {
        & $PipExe install -r $REQUIREMENTS_FILE
        Write-Success "Dependencies installed successfully"
    }
    catch {
        Write-Error-Custom "Failed to install dependencies: $_"
        exit 1
    }
}

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

function Test-EnvironmentConfig {
    Write-Header "Verifying Environment Configuration"

    if (Test-Path $ENV_FILE) {
        Write-Info ".env file already exists"
        Write-Success "Environment configuration is in place"
        return $true
    }
    else {
        Write-Info ".env file not found"
        return $false
    }
}

function New-EnvironmentConfig {
    Write-Header "Creating Environment Configuration Template"

    if (-not (Test-Path $ENV_EXAMPLE_FILE)) {
        Write-Warning ".env.example not found. Creating minimal .env template..."
        $EnvContent = @"
# RAG Assistant Environment Configuration
# Generated: $TIMESTAMP

# Google Gemini API Configuration
GEMINI_API_KEY=your-api-key-here

# Hugging Face API Token (Optional)
HF_TOKEN=your-hf-token-here

# Database Configuration (if using PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_assistant
DB_USER=postgres
DB_PASSWORD=

# Redis Configuration (if using caching)
REDIS_URL=redis://localhost:6379/0

# Logging Configuration
LOG_LEVEL=INFO
DEBUG=false

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4
"@
    }
    else {
        Write-Info "Using template from .env.example"
        $EnvContent = Get-Content $ENV_EXAMPLE_FILE -Raw
    }

    try {
        $EnvContent | Out-File -FilePath $ENV_FILE -Encoding UTF8
        Write-Success "Environment configuration created at $ENV_FILE"
        Write-Warning "Please update $ENV_FILE with your actual configuration values"
    }
    catch {
        Write-Error-Custom "Failed to create .env file: $_"
        exit 1
    }
}

# ============================================================================
# GIT IGNORE PROTECTION
# ============================================================================

function Test-GitIgnoreProtection {
    Write-Header "Verifying Git Ignore Protection"

    if (-not (Test-Path $GITIGNORE_FILE)) {
        Write-Warning ".gitignore file not found"
        return $false
    }

    $GitIgnoreContent = Get-Content $GITIGNORE_FILE -Raw
    $RequiredPatterns = @(
        "\.env",
        "\.venv",
        "__pycache__",
        "\.pytest_cache",
        "\.coverage",
        "htmlcov",
        "dist",
        "build",
        "\.eggs"
    )

    $MissingPatterns = @()
    foreach ($Pattern in $RequiredPatterns) {
        if ($GitIgnoreContent -notmatch [regex]::Escape($Pattern)) {
            $MissingPatterns += $Pattern
        }
    }

    if ($MissingPatterns.Count -eq 0) {
        Write-Success "Git ignore protection is properly configured"
        return $true
    }
    else {
        Write-Warning "Missing patterns in .gitignore: $($MissingPatterns -join ', ')"
        return $false
    }
}

function Add-GitIgnoreProtection {
    Write-Header "Enhancing Git Ignore Protection"

    $GitIgnoreContent = if (Test-Path $GITIGNORE_FILE) {
        Get-Content $GITIGNORE_FILE -Raw
    }
    else {
        "# Git Ignore - RAG Assistant`n`n"
    }

    $AdditionalPatterns = @"

# Python Virtual Environment
.venv/
venv/
env/
ENV/

# Python Cache
__pycache__/
*.py[cod]
*`$py.class
*.so
.Python

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS Files
.DS_Store
Thumbs.db

# Environment Configuration
.env
.env.local
.env.*.local

# Build Artifacts
dist/
build/
*.egg-info/

# Logs
*.log
logs/

# Qdrant Data
qdrant_data/
*.lock
"@

    try {
        $GitIgnoreContent + $AdditionalPatterns | Out-File -FilePath $GITIGNORE_FILE -Encoding UTF8
        Write-Success "Git ignore protection enhanced"
    }
    catch {
        Write-Error-Custom "Failed to update .gitignore: $_"
        exit 1
    }
}

# ============================================================================
# MAIN EXECUTION FLOW
# ============================================================================

function Initialize-Environment {
    Write-Header "RAG Assistant - Environment Bootstrap"
    Write-Info "Timestamp: $TIMESTAMP"
    Write-Info "Project Root: $PROJECT_ROOT"

    # Step 1: Validate system
    Test-SystemRequirements

    # Step 2: Virtual environment
    $VenvExists = Test-VirtualEnvironment
    if (-not $VenvExists) {
        New-VirtualEnvironment
    }

    # Step 3: Update pip
    Update-PipPackage

    # Step 4: Install dependencies
    Install-Dependencies

    # Step 5: Environment configuration
    $EnvConfigExists = Test-EnvironmentConfig
    if (-not $EnvConfigExists) {
        New-EnvironmentConfig
    }

    # Step 6: Git ignore protection
    $GitIgnoreValid = Test-GitIgnoreProtection
    if (-not $GitIgnoreValid) {
        Add-GitIgnoreProtection
    }

    # Final summary
    Write-Header "Bootstrap Complete"
    Write-Success "Environment is ready for development"
    Write-Info "Next steps:"
    Write-Info "  1. Update .env with your API keys"
    Write-Info "  2. Run: .\.venv\Scripts\activate"
    Write-Info "  3. Run: uvicorn app.main:app --reload"
}

# ============================================================================
# ENTRY POINT
# ============================================================================

Initialize-Environment
Write-Host ""

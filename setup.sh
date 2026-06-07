#!/bin/bash

# ============================================================================
# RAG Assistant - Unix/Linux Environment Bootstrap
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
# Usage: bash setup.sh [OPTIONS]
# Options:
#   -f, --force      Force recreation of virtual environment
#   -v, --verbose    Enable verbose output
#   -h, --help       Show this help message
#
# ============================================================================

set -euo pipefail

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"
ENV_EXAMPLE_FILE="${PROJECT_ROOT}/.env.example"
ENV_FILE="${PROJECT_ROOT}/.env"
GITIGNORE_FILE="${PROJECT_ROOT}/.gitignore"

PYTHON_VERSION_REQUIRED="3.11"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

FORCE=false
VERBOSE=false

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -f, --force      Force recreation of virtual environment"
            echo "  -v, --verbose    Enable verbose output"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ============================================================================
# LOGGING UTILITIES
# ============================================================================

write_header() {
    local message="$1"
    echo ""
    echo "===================================="
    echo "$(tput setaf 6)${message}$(tput sgr0)"
    echo "===================================="
}

write_success() {
    local message="$1"
    echo "$(tput setaf 2)✓ ${message}$(tput sgr0)"
}

write_warning() {
    local message="$1"
    echo "$(tput setaf 3)⚠ ${message}$(tput sgr0)" >&2
}

write_error() {
    local message="$1"
    echo "$(tput setaf 1)✗ ${message}$(tput sgr0)" >&2
}

write_info() {
    local message="$1"
    echo "$(tput setaf 6)ℹ ${message}$(tput sgr0)"
}

# ============================================================================
# SYSTEM VALIDATION
# ============================================================================

test_system_requirements() {
    write_header "Validating System Requirements"

    # Check Python installation
    if ! command -v python3 &> /dev/null; then
        write_error "Python3 not found. Please install Python 3.11+ from https://www.python.org/"
        exit 1
    fi

    local python_version=$(python3 --version 2>&1)
    write_info "Detected: ${python_version}"
    write_success "Python is installed"

    # Check Git installation
    if ! command -v git &> /dev/null; then
        write_error "Git not found. Please install Git from https://git-scm.com/"
        exit 1
    fi

    local git_version=$(git --version 2>&1)
    write_info "Detected: ${git_version}"
    write_success "Git is installed"

    # Verify project structure
    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        write_error "requirements.txt not found at $REQUIREMENTS_FILE"
        exit 1
    fi
    write_success "Project structure verified"
}

# ============================================================================
# VIRTUAL ENVIRONMENT MANAGEMENT
# ============================================================================

test_virtual_environment() {
    write_header "Checking Virtual Environment"

    if [[ -d "$VENV_DIR" ]]; then
        write_info "Virtual environment exists at $VENV_DIR"

        # Test if venv is functional
        local python_exe="${VENV_DIR}/bin/python"
        if [[ -f "$python_exe" ]]; then
            write_success "Virtual environment is valid and ready"
            return 0
        else
            write_warning "Virtual environment exists but appears corrupted"
            if [[ "$FORCE" == true ]]; then
                write_info "Force flag set. Removing corrupted venv..."
                rm -rf "$VENV_DIR"
                return 1
            else
                write_warning "Run with --force to recreate. Exiting."
                exit 1
            fi
        fi
    else
        write_info "No virtual environment found"
        return 1
    fi
}

new_virtual_environment() {
    write_header "Creating Virtual Environment"

    write_info "Running: python3 -m venv $VENV_DIR"
    if python3 -m venv "$VENV_DIR"; then
        write_success "Virtual environment created successfully"
    else
        write_error "Failed to create virtual environment"
        exit 1
    fi
}

# ============================================================================
# DEPENDENCY MANAGEMENT
# ============================================================================

update_pip_package() {
    write_header "Upgrading pip Package Manager"

    local python_exe="${VENV_DIR}/bin/python"
    local pip_exe="${VENV_DIR}/bin/pip"

    if [[ ! -f "$pip_exe" ]]; then
        write_error "pip executable not found. Virtual environment may be corrupted."
        exit 1
    fi

    write_info "Upgrading pip to latest version..."
    if "$python_exe" -m pip install --upgrade pip; then
        write_success "pip upgraded successfully"
    else
        write_error "Failed to upgrade pip"
        exit 1
    fi
}

install_dependencies() {
    write_header "Installing Project Dependencies"

    local pip_exe="${VENV_DIR}/bin/pip"

    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        write_error "requirements.txt not found"
        exit 1
    fi

    write_info "Installing packages from requirements.txt..."
    if "$pip_exe" install -r "$REQUIREMENTS_FILE"; then
        write_success "Dependencies installed successfully"
    else
        write_error "Failed to install dependencies"
        exit 1
    fi
}

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================

test_environment_config() {
    write_header "Verifying Environment Configuration"

    if [[ -f "$ENV_FILE" ]]; then
        write_info ".env file already exists"
        write_success "Environment configuration is in place"
        return 0
    else
        write_info ".env file not found"
        return 1
    fi
}

new_environment_config() {
    write_header "Creating Environment Configuration Template"

    if [[ -f "$ENV_EXAMPLE_FILE" ]]; then
        write_info "Using template from .env.example"
        cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    else
        write_warning ".env.example not found. Creating minimal .env template..."
        cat > "$ENV_FILE" << 'EOF'
# RAG Assistant Environment Configuration
# Generated: $(date '+%Y-%m-%d %H:%M:%S')

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
EOF
    fi

    if [[ $? -eq 0 ]]; then
        write_success "Environment configuration created at $ENV_FILE"
        write_warning "Please update $ENV_FILE with your actual configuration values"
    else
        write_error "Failed to create .env file"
        exit 1
    fi
}

# ============================================================================
# GIT IGNORE PROTECTION
# ============================================================================

test_gitignore_protection() {
    write_header "Verifying Git Ignore Protection"

    if [[ ! -f "$GITIGNORE_FILE" ]]; then
        write_warning ".gitignore file not found"
        return 1
    fi

    local required_patterns=(
        "\.env"
        "\.venv"
        "__pycache__"
        "\.pytest_cache"
        "\.coverage"
        "htmlcov"
        "dist"
        "build"
        "\.eggs"
    )

    local missing_patterns=()
    for pattern in "${required_patterns[@]}"; do
        if ! grep -q "$pattern" "$GITIGNORE_FILE"; then
            missing_patterns+=("$pattern")
        fi
    done

    if [[ ${#missing_patterns[@]} -eq 0 ]]; then
        write_success "Git ignore protection is properly configured"
        return 0
    else
        write_warning "Missing patterns in .gitignore: $(printf '%s, ' "${missing_patterns[@]}" | sed 's/, $//')"
        return 1
    fi
}

add_gitignore_protection() {
    write_header "Enhancing Git Ignore Protection"

    # Check if .gitignore exists and has content
    if [[ -f "$GITIGNORE_FILE" ]]; then
        local content=$(cat "$GITIGNORE_FILE")
    else
        local content="# Git Ignore - RAG Assistant"
    fi

    # Append additional patterns
    cat >> "$GITIGNORE_FILE" << 'EOF'

# Python Virtual Environment
.venv/
venv/
env/
ENV/

# Python Cache
__pycache__/
*.py[cod]
*$py.class
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
EOF

    if [[ $? -eq 0 ]]; then
        write_success "Git ignore protection enhanced"
    else
        write_error "Failed to update .gitignore"
        exit 1
    fi
}

# ============================================================================
# MAIN EXECUTION FLOW
# ============================================================================

initialize_environment() {
    write_header "RAG Assistant - Environment Bootstrap"
    write_info "Timestamp: $TIMESTAMP"
    write_info "Project Root: $PROJECT_ROOT"

    # Step 1: Validate system
    test_system_requirements

    # Step 2: Virtual environment
    if test_virtual_environment; then
        write_info "Using existing virtual environment"
    else
        new_virtual_environment
    fi

    # Step 3: Update pip
    update_pip_package

    # Step 4: Install dependencies
    install_dependencies

    # Step 5: Environment configuration
    if ! test_environment_config; then
        new_environment_config
    fi

    # Step 6: Git ignore protection
    if ! test_gitignore_protection; then
        add_gitignore_protection
    fi

    # Final summary
    write_header "Bootstrap Complete"
    write_success "Environment is ready for development"
    write_info "Next steps:"
    write_info "  1. Update .env with your API keys"
    write_info "  2. Run: source .venv/bin/activate"
    write_info "  3. Run: uvicorn app.main:app --reload"
}

# ============================================================================
# ENTRY POINT
# ============================================================================

initialize_environment
echo ""

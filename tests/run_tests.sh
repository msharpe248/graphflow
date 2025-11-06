#!/bin/bash

# GraphFlow Test Runner
# Convenience script for running different test suites
# Run from project root or tests directory

set -e  # Exit on error

# Change to project root if we're in tests directory
if [[ $(basename "$PWD") == "tests" ]]; then
    cd ..
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    if ! command_exists pytest; then
        print_error "pytest not found. Installing..."
        pip install pytest pytest-asyncio httpx requests pytest-cov pytest-timeout
    fi

    if ! command_exists graphflow-compile; then
        print_warn "graphflow-compile not found. Installing packages..."
        pip install -e packages/graph-core
        pip install -e packages/graph-compiler
        pip install -e packages/graph-runtime
    fi

    print_info "Prerequisites OK"
}

# Function to run compilation tests
run_compilation_tests() {
    print_info "Running compilation tests..."
    pytest tests/test_compilation.py -v "$@"
}

# Function to run standalone tests
run_standalone_tests() {
    print_info "Running standalone execution tests..."
    print_warn "Note: This will start FastAPI servers on ports 18765+..."
    pytest tests/test_standalone_execution.py -v "$@"
}

# Function to run runtime tests
run_runtime_tests() {
    print_info "Running runtime execution tests..."
    print_warn "Note: This will start a runtime server on port 18700..."
    pytest tests/test_runtime_execution.py -v "$@"
}

# Function to run all tests
run_all_tests() {
    print_info "Running all tests..."
    pytest tests/ -v "$@"
}

# Function to run tests with coverage
run_with_coverage() {
    print_info "Running tests with coverage..."
    pytest tests/ -v \
        --cov=graphflow_core \
        --cov=graphflow_compiler \
        --cov=graphflow_runtime \
        --cov-report=term \
        --cov-report=html \
        "$@"

    print_info "Coverage report saved to htmlcov/index.html"
}

# Function to show usage
show_usage() {
    cat << EOF
GraphFlow Test Runner

Usage: ./run_tests.sh [COMMAND] [OPTIONS]

Commands:
    all             Run all tests (default)
    compilation     Run compilation tests only
    standalone      Run standalone execution tests only
    runtime         Run runtime execution tests only
    coverage        Run all tests with coverage report
    check           Check prerequisites and setup
    help            Show this help message

Options:
    Any additional options are passed to pytest

Examples:
    ./run_tests.sh                          # Run all tests
    ./run_tests.sh compilation              # Run compilation tests
    ./run_tests.sh coverage                 # Run with coverage
    ./run_tests.sh all -k "pydantic"        # Run tests matching "pydantic"
    ./run_tests.sh compilation -v -s        # Run with verbose output
    ./run_tests.sh all -m "not slow"        # Skip slow tests

EOF
}

# Main script
main() {
    # Default command
    COMMAND="${1:-all}"
    shift || true  # Remove first argument if exists

    case "$COMMAND" in
        check)
            check_prerequisites
            ;;
        compilation)
            check_prerequisites
            run_compilation_tests "$@"
            ;;
        standalone)
            check_prerequisites
            run_standalone_tests "$@"
            ;;
        runtime)
            check_prerequisites
            run_runtime_tests "$@"
            ;;
        all)
            check_prerequisites
            run_all_tests "$@"
            ;;
        coverage)
            check_prerequisites
            run_with_coverage "$@"
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

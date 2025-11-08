#!/bin/bash
# Pre-commit check to ensure packages are in editable mode

RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "Checking if packages are in editable mode..."

NOT_EDITABLE=0

check_package() {
    local package=$1
    if pip show $package 2>/dev/null | grep Location | grep -q "site-packages"; then
        echo -e "${RED}✗ $package is NOT in editable mode${NC}"
        NOT_EDITABLE=1
    fi
}

check_package "graphflow-core"
check_package "graphflow-plugins-ai"
check_package "graphflow-plugins-http"
check_package "graphflow-plugin-example"
check_package "graphflow-runtime"

if [ $NOT_EDITABLE -eq 1 ]; then
    echo ""
    echo -e "${YELLOW}WARNING: Some packages are not in editable mode!${NC}"
    echo -e "${YELLOW}Your code changes may not take effect.${NC}"
    echo ""
    echo "Run: make install"
    echo ""
    exit 1
fi

echo "✓ All packages are in editable mode"
exit 0

#!/bin/bash

# COFFE Mac Setup Script
# Run this from the root of the Coffe repo:
#   chmod +x setup_mac.sh
#   ./setup_mac.sh

set -e  # exit immediately on any error

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo -e "${BLUE}========================================"
echo -e "   COFFE Mac Setup"
echo -e "========================================${NC}"
echo ""

# ─── Verify we're in the repo root ────────────────────────────────────────────

if [ ! -f "Dockerfile" ] || [ ! -f "setup.py" ]; then
    echo -e "${RED}Error: Run this script from the root of the Coffe repo.${NC}"
    echo "Example:  cd Coffe-3Llamas && ./setup_mac.sh"
    exit 1
fi

REPO_DIR=$(pwd)
WORKSPACE_DIR=$(dirname "$REPO_DIR")
REPO_NAME=$(basename "$REPO_DIR")

echo "Repo:      $REPO_DIR"
echo "Workspace: $WORKSPACE_DIR"
echo ""

# ─── Prerequisite checks ──────────────────────────────────────────────────────

echo -e "${BLUE}Checking prerequisites...${NC}"
echo ""

# Python 3.10+
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
PYTHON_VERSION="$PYTHON_MAJOR.$PYTHON_MINOR"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "${RED}✗ Python 3.10+ required. Found Python $PYTHON_VERSION.${NC}"
    echo "  Install a newer version from https://python.org or via: brew install python@3.11"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"

# Docker installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found.${NC}"
    echo "  Install Docker Desktop for Mac from https://www.docker.com/products/docker-desktop/"
    exit 1
fi
echo -e "${GREEN}✓ Docker installed${NC}"

# Docker running
if ! docker info &> /dev/null 2>&1; then
    echo -e "${RED}✗ Docker Desktop is not running.${NC}"
    echo "  Open Docker Desktop, wait until the menu bar icon shows 'Running', then try again."
    exit 1
fi
echo -e "${GREEN}✓ Docker Desktop is running${NC}"

# pipenv installed
if ! command -v pipenv &> /dev/null; then
    echo -e "${RED}✗ pipenv not found.${NC}"
    echo "  Install it with: pip install pipenv"
    exit 1
fi
echo -e "${GREEN}✓ pipenv found${NC}"

echo ""

# ─── Step 1: Install coffe ────────────────────────────────────────────────────

echo -e "${BLUE}[Step 1/3] Installing coffe into pipenv...${NC}"
pipenv run pip install -e .
echo -e "${GREEN}✓ coffe installed (editable mode — code changes apply instantly)${NC}"
echo ""

# ─── Step 2: Build Docker image ───────────────────────────────────────────────

echo -e "${BLUE}[Step 2/3] Building Docker image...${NC}"
echo -e "${YELLOW}Note: You will see a warning about CPU instruction counting — this is expected on Mac.${NC}"
echo ""
echo "running: docker build --no-cache . -t coffe"
docker build --no-cache . -t coffe
echo ""
echo -e "${GREEN}✓ Docker image built${NC}"
echo ""

# ─── Step 3: Initialize coffe ─────────────────────────────────────────────────

echo -e "${BLUE}[Step 3/3] Initializing coffe...${NC}"
echo -e "${YELLOW}Note: The yellow warning below about instruction counting is expected on Mac.${NC}"
echo ""
cd "$WORKSPACE_DIR"
pipenv run coffe init \
    -d "$REPO_NAME/datasets" \
    -w "$WORKSPACE_DIR" \
    -p "$REPO_NAME/perf.json"
echo ""
echo -e "${GREEN}✓ coffe initialized — coffe_init.json written to $WORKSPACE_DIR${NC}"

# ─── Done ─────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}========================================"
echo -e "   Setup complete!"
echo -e "========================================${NC}"
echo ""
echo "To run an evaluation, open a new terminal and run:"
echo ""
echo -e "  cd $WORKSPACE_DIR"
echo -e "  coffe pipe function $REPO_NAME/examples/function \\"
echo -e "    -p $REPO_NAME/examples/function/GPT-4o.json \\"
echo -e "    -f efficient_at_1 \\"
echo -e "    -n 4 \\"
echo -e "    --measure time"
echo ""
echo -e "${YELLOW}Reminder: Docker Desktop must be open and running before each evaluation.${NC}"
echo ""
#!/usr/bin/env bash
# First-time setup: builds Docker images and downloads genome data.
# After this completes, run: docker compose up -d
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env so DATA_DIR and other vars set there are available to this script
if [ -f .env ]; then
    set -o allexport
    # shellcheck disable=SC1091
    source .env
    set +o allexport
fi

DATA_DIR="${DATA_DIR:-/opt/fastvep/data}"
TIER="${1:-full}"   # full | clinical | minimal

echo "=== fastVEP Setup ==="
echo "Data directory : $DATA_DIR"
echo "Genome tier    : $TIER"
echo ""

# --- Step 1: env file ---
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[1/3] Created .env from .env.example (edit if needed)"
else
    echo "[1/3] .env already exists — skipping"
fi

# --- Step 2: build Docker image (includes fastvep + fastvep-web binaries) ---
echo "[2/3] Building Docker image (Rust compile — ~15 min first time)..."
docker compose build fastvep-web

# --- Step 3: download + build genome data ---
echo "[3/3] Setting up genome data (tier: $TIER)..."
echo "      Host path      : $DATA_DIR"
echo "      Container path : /opt/fastvep/data (inside the setup container)"
mkdir -p "$DATA_DIR"   # must exist on host before Docker mounts it

docker compose run --rm \
    -v "$DATA_DIR":/opt/fastvep/data \
    -e FASTVEP_BIN=/usr/local/bin \
    -e FASTVEP_YES=1 \
    -e HOST_DATA_DIR="$DATA_DIR" \
    --entrypoint bash \
    fastvep-web "/scripts/deploy-${TIER}.sh"

echo ""
echo "=== Setup complete ==="
echo "Start the stack with:"
echo "  docker compose up -d"

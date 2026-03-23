#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# KISWARM7 - Download Pip Wheels for Offline Installation
# ═══════════════════════════════════════════════════════════════════════════════
# This script downloads all Python dependency wheels for offline installation.
#
# Usage:
#   ./download_wheels.sh [--minimal]
#
# Options:
#   --minimal    Download only essential packages (faster, smaller)
#   --full       Download all packages including ML/AI (larger)
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OFFLINE_DIR="$(dirname "$SCRIPT_DIR")"
WHEELS_DIR="$OFFLINE_DIR/pip_wheels"
REQ_FILE="$OFFLINE_DIR/requirements-offline.txt"

MINIMAL=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --minimal)
            MINIMAL=true
            shift
            ;;
        --full)
            MINIMAL=false
            shift
            ;;
    esac
done

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "     KISWARM7 - Pip Wheel Downloader"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "  Offline Dir: $OFFLINE_DIR"
echo "  Wheels Dir:  $WHEELS_DIR"
echo "  Minimal:     $MINIMAL"
echo ""

# Create wheels directory
mkdir -p "$WHEELS_DIR"

if [ "$MINIMAL" = true ]; then
    echo "[INFO] Downloading MINIMAL essential packages..."
    
    # Essential packages only
    pip download -d "$WHEELS_DIR" \
        flask==3.0.2 \
        flask-cors==4.0.0 \
        requests==2.31.0 \
        rich==13.7.1 \
        psutil==5.9.8 \
        pydantic==2.6.3 \
        cryptography==42.0.5 \
        pyjwt==2.8.0 \
        aiohttp==3.9.3 \
        structlog==24.1.0 \
        pytest==8.1.1 \
        pyngrok==7.1.2 \
        2>/dev/null || echo "[WARN] Some packages may have dependency conflicts"
else
    echo "[INFO] Downloading FULL package set..."
    
    if [ -f "$REQ_FILE" ]; then
        echo "[INFO] Using requirements file: $REQ_FILE"
        pip download -r "$REQ_FILE" -d "$WHEELS_DIR" 2>/dev/null || {
            echo "[WARN] Some packages failed - trying individually..."
            # Try to download packages one by one
            while IFS= read -r line; do
                # Skip comments and empty lines
                [[ "$line" =~ ^#.*$ ]] && continue
                [[ -z "$line" ]] && continue
                
                pkg=$(echo "$line" | sed 's/==.*//' | sed 's/>=.*//' | sed 's/<.*//' | tr -d ' ')
                if [ -n "$pkg" ]; then
                    echo "  Downloading: $pkg"
                    pip download "$pkg" -d "$WHEELS_DIR" 2>/dev/null || true
                fi
            done < "$REQ_FILE"
        }
    else
        echo "[ERROR] Requirements file not found: $REQ_FILE"
        exit 1
    fi
fi

# Count wheels
WHEEL_COUNT=$(find "$WHEELS_DIR" -name "*.whl" | wc -l)
TOTAL_SIZE=$(du -sh "$WHEELS_DIR" | cut -f1)

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  DOWNLOAD COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "  📦 Wheels Downloaded: $WHEEL_COUNT"
echo "  💾 Total Size: $TOTAL_SIZE"
echo "  📁 Location: $WHEELS_DIR"
echo ""
echo "  To install offline:"
echo "    pip install --no-index --find-links=$WHEELS_DIR -r $REQ_FILE"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"

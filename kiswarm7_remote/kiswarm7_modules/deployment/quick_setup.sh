#!/bin/bash
#
# KISWARM7.0 Quick Setup - Simplified Version
# ============================================
# 
# For quick local testing without full server setup
#

set -e

echo "🜂 KISWARM7.0 Quick Setup"
echo "========================="

# Create directories
mkdir -p /opt/kiswarm7/{identity,autonomous,sensory,deployment,hooks,logs}
mkdir -p /var/log/kiswarm7

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Installing Python..."
    apt-get update -qq
    apt-get install -y python3 python3-pip python3-venv -qq
fi

# Create venv
cd /opt/kiswarm7
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate

# Install required packages
pip install -q psutil pyyaml python-dateutil

# Copy modules if not exists
if [ ! -f "/opt/kiswarm7/modules/bridge/__init__.py" ]; then
    echo "Modules need to be copied from source"
    echo "Run from your development machine:"
    echo "  scp -r kiswarm7_modules/* root@your-server:/opt/kiswarm7/modules/"
fi

echo ""
echo "Setup complete. Start with:"
echo "  cd /opt/kiswarm7 && source venv/bin/activate"
echo "  python -m modules.bridge.m101_persistent_identity_anchor"

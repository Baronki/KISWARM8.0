#!/bin/bash
# Setup GitHub Actions Self-Hosted Runner
# Run this ONCE on the UpCloud server

# Get token from: https://github.com/Baronki/KISWARM7/settings/actions/runners/new
# Replace YOUR_TOKEN below

RUNNER_TOKEN="YOUR_RUNNER_TOKEN"

mkdir -p /opt/actions-runner && cd /opt/actions-runner

# Download runner
curl -o actions-runner-linux-x64-2.321.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz

tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz

# Configure
./config.sh --url https://github.com/Baronki/KISWARM7 --token $RUNNER_TOKEN --name kiswarm7-runner --labels self-hosted

# Install as service
./svc.sh install
./svc.sh start

echo "Runner installed and started!"

/**
 * Master KISWARM API - Tunnel Management Endpoint
 * 
 * Manages ngrok tunnels for external connectivity
 * Allows installers from Colab/cloud to connect to Master API
 */

import { NextRequest, NextResponse } from 'next/server';

// Tunnel status tracking
interface TunnelStatus {
  active: boolean;
  publicUrl: string | null;
  createdAt: string | null;
  lastChecked: string;
}

let tunnelStatus: TunnelStatus = {
  active: false,
  publicUrl: null,
  createdAt: null,
  lastChecked: new Date().toISOString(),
};

export async function GET() {
  // Check if we're in a browser-accessible environment
  // For Colab connectivity, the Master API URL should be set via environment
  const masterUrl = process.env.MASTER_PUBLIC_URL || process.env.NGROK_URL || null;
  
  // Update tunnel status
  if (masterUrl) {
    tunnelStatus = {
      active: true,
      publicUrl: masterUrl,
      createdAt: tunnelStatus.createdAt || new Date().toISOString(),
      lastChecked: new Date().toISOString(),
    };
  }
  
  return NextResponse.json({
    tunnel: tunnelStatus,
    instructions: getTunnelInstructions(),
    deployment_command: getDeploymentCommand(tunnelStatus.publicUrl),
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, public_url } = body;
    
    switch (action) {
      case 'set_public_url':
        // Set the public URL for the Master API (called when ngrok is started)
        tunnelStatus = {
          active: true,
          publicUrl: public_url,
          createdAt: new Date().toISOString(),
          lastChecked: new Date().toISOString(),
        };
        
        return NextResponse.json({
          status: 'success',
          message: 'Public URL set',
          tunnel: tunnelStatus,
        });
        
      case 'clear_tunnel':
        tunnelStatus = {
          active: false,
          publicUrl: null,
          createdAt: null,
          lastChecked: new Date().toISOString(),
        };
        
        return NextResponse.json({
          status: 'success',
          message: 'Tunnel cleared',
        });
        
      default:
        return NextResponse.json({
          status: 'error',
          message: 'Unknown action',
        }, { status: 400 });
    }
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

function getTunnelInstructions(): string[] {
  return [
    '# Option 1: Use ngrok to expose local Master API',
    '# Install ngrok: https://ngrok.com/download',
    '',
    '# Start tunnel (replace 3000 with your local port)',
    'ngrok http 3000',
    '',
    '# Copy the https URL (e.g., https://abc123.ngrok.io)',
    '# Set as environment variable:',
    'export MASTER_PUBLIC_URL="https://abc123.ngrok.io"',
    '',
    '# Option 2: Use cloudflare tunnel',
    'cloudflared tunnel --url http://localhost:3000',
    '',
    '# Option 3: Use pyngrok in Colab',
    'from pyngrok import ngrok',
    'public_url = ngrok.connect(3000).public_url',
    'print(f"Master API: {public_url}")',
  ];
}

function getDeploymentCommand(publicUrl: string | null): string {
  const masterUrl = publicUrl || 'YOUR_MASTER_URL_HERE';
  
  return `# KISWARM Autonomous Deployment (Colab)

# 1. Download installer
!curl -fsSL https://raw.githubusercontent.com/Baronki/KISWARM6.0/main/kiinstaller/autonomous_kiswarm_installer.py -o autonomous_kiswarm_installer.py

# 2. Install dependencies
!pip install -q flask flask-cors structlog requests pyngrok

# 3. Deploy with Master API connection
from autonomous_kiswarm_installer import autonomous_deploy
result = autonomous_deploy(
    master_url="${masterUrl}"
)

# The installer will automatically:
# - Register with Master KISWARM
# - Report deployment progress
# - Request support if issues occur
# - Verify complete system setup`;
}

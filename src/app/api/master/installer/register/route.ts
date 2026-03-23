/**
 * Master KISWARM API - Installer Registration Endpoint
 * 
 * This endpoint receives registration requests from KISWARM installers
 * deployed in the wild (Colab, cloud, edge devices, etc.)
 */

import { NextRequest, NextResponse } from 'next/server';

// In-memory store for connected installers (use database in production)
const connectedInstallers: Map<string, InstallerInfo> = new Map();

interface InstallerInfo {
  entityId: string;
  identity: {
    entity_id: string;
    created_at: string;
    environment: string;
    hostname: string;
    platform: string;
    python_version: string;
  };
  registeredAt: string;
  lastSeen: string;
  status: 'active' | 'idle' | 'offline';
  progress: ProgressUpdate[];
  issues: IssueReport[];
}

interface ProgressUpdate {
  phase: string;
  status: string;
  progress: number;
  message: string;
  timestamp: string;
  details: Record<string, unknown>;
}

interface IssueReport {
  issue: string;
  context: Record<string, unknown>;
  timestamp: string;
  resolved: boolean;
  resolution?: string;
}

// Master KISWARM Identity
const MASTER_ID = `master_kiswarm_${Date.now().toString(36)}`;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, entity_id, identity, timestamp } = body;

    if (action === 'register') {
      // Register new installer
      const installerInfo: InstallerInfo = {
        entityId: entity_id,
        identity: identity,
        registeredAt: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        status: 'active',
        progress: [],
        issues: [],
      };

      connectedInstallers.set(entity_id, installerInfo);

      console.log(`[MASTER] New installer registered: ${entity_id}`);
      console.log(`[MASTER] Environment: ${identity.environment}`);
      console.log(`[MASTER] Platform: ${identity.platform}`);

      // Trigger Watchtower notification
      triggerWatchtowerAlert('new_installer', installerInfo);

      return NextResponse.json({
        status: 'success',
        master_id: MASTER_ID,
        message: 'Installer registered successfully',
        registered_at: installerInfo.registeredAt,
        instructions: getDeploymentInstructions(identity.environment),
      });
    }

    return NextResponse.json({
      status: 'error',
      message: 'Invalid action',
    }, { status: 400 });

  } catch (error) {
    console.error('[MASTER] Registration error:', error);
    return NextResponse.json({
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function GET() {
  // Return list of connected installers
  const installers = Array.from(connectedInstallers.values());
  
  return NextResponse.json({
    master_id: MASTER_ID,
    total_installers: installers.length,
    active_installers: installers.filter(i => i.status === 'active').length,
    installers: installers.map(i => ({
      entity_id: i.entityId,
      environment: i.identity.environment,
      registered_at: i.registeredAt,
      last_seen: i.lastSeen,
      status: i.status,
      progress_count: i.progress.length,
    })),
  });
}

function getDeploymentInstructions(environment: string): string[] {
  const baseInstructions = [
    'Monitor installer progress through /api/master/installer/progress',
    'Report any issues through /api/master/installer/support',
    'Send heartbeats every 30 seconds to /api/master/installer/heartbeat',
  ];

  if (environment === 'COLAB') {
    return [
      ...baseInstructions,
      'For Ollama issues in Colab, use the fallback installation method',
      'GPU acceleration available - pull CUDA-enabled models',
    ];
  }

  return baseInstructions;
}

function triggerWatchtowerAlert(type: string, data: unknown) {
  // This would integrate with the Watchtower Guard
  // For now, we log it
  console.log(`[WATCHTOWER ALERT] Type: ${type}`);
  console.log(`[WATCHTOWER ALERT] Data:`, JSON.stringify(data, null, 2));
}

// Export for use by other endpoints
export { connectedInstallers, MASTER_ID };

/**
 * Master KISWARM API - Installer Heartbeat Endpoint
 * 
 * Receives heartbeat signals from installers to track online status
 */

import { NextRequest, NextResponse } from 'next/server';
import { connectedInstallers } from '../register/route';

// Heartbeat timeout in milliseconds (5 minutes)
const HEARTBEAT_TIMEOUT = 5 * 60 * 1000;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { entity_id, timestamp, status } = body;

    if (!entity_id) {
      return NextResponse.json({
        status: 'error',
        message: 'Missing entity_id',
      }, { status: 400 });
    }

    // Update installer heartbeat
    const installer = connectedInstallers.get(entity_id);
    
    if (installer) {
      installer.lastSeen = new Date().toISOString();
      installer.status = status || 'active';
    } else {
      // Auto-register unknown installer
      const autoRegister = {
        entityId: entity_id,
        identity: {
          entity_id: entity_id,
          created_at: timestamp || new Date().toISOString(),
          environment: 'unknown',
          hostname: 'unknown',
          platform: 'unknown',
          python_version: 'unknown',
        },
        registeredAt: new Date().toISOString(),
        lastSeen: new Date().toISOString(),
        status: 'active' as const,
        progress: [],
        issues: [],
      };
      connectedInstallers.set(entity_id, autoRegister);
    }

    // Update all installer statuses based on last heartbeat
    updateInstallerStatuses();

    return NextResponse.json({
      status: 'success',
      message: 'Heartbeat received',
      server_time: new Date().toISOString(),
    });

  } catch (error) {
    console.error('[MASTER] Heartbeat error:', error);
    return NextResponse.json({
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function GET() {
  updateInstallerStatuses();

  const installers = Array.from(connectedInstallers.values());
  
  const active = installers.filter(i => i.status === 'active');
  const idle = installers.filter(i => i.status === 'idle');
  const offline = installers.filter(i => i.status === 'offline');

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    total_installers: installers.length,
    active: active.length,
    idle: idle.length,
    offline: offline.length,
    installers: installers.map(i => ({
      entity_id: i.entityId,
      environment: i.identity.environment,
      hostname: i.identity.hostname,
      status: i.status,
      last_seen: i.lastSeen,
      registered_at: i.registeredAt,
      seconds_since_heartbeat: Math.floor((Date.now() - new Date(i.lastSeen).getTime()) / 1000),
    })),
  });
}

function updateInstallerStatuses() {
  const now = Date.now();
  
  for (const [_, installer] of connectedInstallers) {
    const lastSeen = new Date(installer.lastSeen).getTime();
    const timeSinceLastSeen = now - lastSeen;

    if (timeSinceLastSeen > HEARTBEAT_TIMEOUT) {
      installer.status = 'offline';
    } else if (timeSinceLastSeen > HEARTBEAT_TIMEOUT / 2) {
      installer.status = 'idle';
    } else {
      installer.status = 'active';
    }
  }
}

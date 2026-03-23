/**
 * Legacy Mesh API - Status Update Endpoint
 * 
 * Handles status updates from installers
 * Route: /api/mesh/status/[installer_id]
 */

import { NextRequest, NextResponse } from 'next/server';

// Get the shared registry from the register endpoint
declare global {
  var meshInstallers: Map<string, any>;
}

// Initialize global registry if not exists
if (!globalThis.meshInstallers) {
  globalThis.meshInstallers = new Map();
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ installer_id: string }> }
) {
  try {
    const { installer_id } = await params;
    const body = await request.json();
    
    const installer = globalThis.meshInstallers.get(installer_id);
    
    if (!installer) {
      // Auto-register if not found
      const newInstaller = {
        installer_id,
        installer_name: installer_id,
        environment: 'unknown',
        capabilities: [],
        registered_at: new Date().toISOString(),
        last_seen: new Date().toISOString(),
        status: body.status || 'unknown',
        progress: [],
        errors: [],
      };
      globalThis.meshInstallers.set(installer_id, newInstaller);
    } else {
      // Update existing installer
      installer.last_seen = new Date().toISOString();
      installer.status = body.status || installer.status;
      
      if (body.task && body.progress !== undefined) {
        installer.progress.push({
          task: body.task,
          progress: body.progress,
          timestamp: new Date().toISOString(),
        });
      }
    }
    
    console.log(`[MESH] Status update from ${installer_id}: ${body.status} - ${body.task || 'no task'} (${body.progress || 0}%)`);
    
    return NextResponse.json({
      status: "received",
      installer_id,
      message: "Status updated",
    });
    
  } catch (error) {
    return NextResponse.json({
      status: "error",
      message: error instanceof Error ? error.message : "Unknown error",
    }, { status: 500 });
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ installer_id: string }> }
) {
  const { installer_id } = await params;
  const installer = globalThis.meshInstallers.get(installer_id);
  
  if (!installer) {
    return NextResponse.json({
      status: "not_found",
      message: `Installer ${installer_id} not registered`,
    }, { status: 404 });
  }
  
  return NextResponse.json({
    installer_id,
    status: installer.status,
    progress: installer.progress,
    errors: installer.errors,
    last_seen: installer.last_seen,
  });
}

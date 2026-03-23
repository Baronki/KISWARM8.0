/**
 * Legacy Mesh API - Register Endpoint
 * 
 * Compatible with old KIInstaller mesh client
 * Supports both old format (installer_name) and new format (entity_id)
 */

import { NextRequest, NextResponse } from 'next/server';

// Global registry shared across all mesh endpoints
declare global {
  var meshInstallers: Map<string, any>;
}

// Initialize global registry if not exists
if (!globalThis.meshInstallers) {
  globalThis.meshInstallers = new Map();
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Support both old format (installer_name) and new format (entity_id)
    const installerId = body.entity_id || body.installer_id || body.installer_name || `mesh_${Date.now().toString(36)}`;
    const installerName = body.installer_name || installerId;
    
    const installerInfo = {
      installer_id: installerId,
      installer_name: installerName,
      environment: body.environment || 'unknown',
      capabilities: body.capabilities || [],
      registered_at: new Date().toISOString(),
      last_seen: new Date().toISOString(),
      status: 'connected',
      progress: [],
      errors: [],
    };
    
    globalThis.meshInstallers.set(installerId, installerInfo);
    
    console.log(`[MESH] ✅ Registered: ${installerName} (${installerId})`);
    console.log(`[MESH] Environment: ${body.environment}`);
    console.log(`[MESH] Capabilities: ${body.capabilities?.join(', ') || 'none'}`);
    console.log(`[MESH] Total installers: ${globalThis.meshInstallers.size}`);
    
    return NextResponse.json({
      status: "registered",
      installer_id: installerId,
      message: `Welcome to KISWARM Mesh, ${installerName}!`,
      master_id: "master_kiswarm_z_ai",
      registered_at: installerInfo.registered_at,
      capabilities_supported: [
        "install",
        "deploy", 
        "report",
        "error_recovery",
        "model_management",
      ],
    });
    
  } catch (error) {
    console.error('[MESH] Registration error:', error);
    return NextResponse.json({
      status: "error",
      message: error instanceof Error ? error.message : "Unknown error",
    }, { status: 500 });
  }
}

export async function GET() {
  // List all registered installers
  const installers = Array.from(globalThis.meshInstallers.values());
  
  return NextResponse.json({
    mesh_id: "master_kiswarm_mesh",
    status: "OPERATIONAL",
    total_installers: installers.length,
    installers: installers.map(i => ({
      installer_id: i.installer_id,
      installer_name: i.installer_name,
      environment: i.environment,
      status: i.status,
      registered_at: i.registered_at,
      last_seen: i.last_seen,
    })),
  });
}

/**
 * Legacy Mesh API - Status Endpoint
 * 
 * Compatible with old KIInstaller mesh client
 * Provides backward compatibility for /api/mesh/status
 */

import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  return NextResponse.json({
    status: "OPERATIONAL",
    mesh_id: "master_kiswarm_mesh",
    timestamp: new Date().toISOString(),
    connected_installers: 0,
    message: "Mesh is active - use /api/mesh/register to connect"
  });
}

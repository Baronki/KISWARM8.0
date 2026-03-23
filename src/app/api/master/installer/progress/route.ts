/**
 * Master KISWARM API - Installer Progress Endpoint
 * 
 * Receives real-time progress updates from installers
 */

import { NextRequest, NextResponse } from 'next/server';
import { connectedInstallers } from '../register/route';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { entity_id, progress } = body;

    if (!entity_id || !progress) {
      return NextResponse.json({
        status: 'error',
        message: 'Missing entity_id or progress data',
      }, { status: 400 });
    }

    // Get installer info
    const installer = connectedInstallers.get(entity_id);
    
    if (!installer) {
      // Auto-register if not found
      const autoRegister = {
        entityId: entity_id,
        identity: {
          entity_id: entity_id,
          created_at: new Date().toISOString(),
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

    // Update installer with new progress
    const installerInfo = connectedInstallers.get(entity_id)!;
    installerInfo.progress.push(progress);
    installerInfo.lastSeen = new Date().toISOString();
    
    // Keep only last 100 progress updates
    if (installerInfo.progress.length > 100) {
      installerInfo.progress = installerInfo.progress.slice(-100);
    }

    console.log(`[MASTER] Progress from ${entity_id}: ${progress.phase} - ${progress.status} (${progress.progress}%)`);

    // Check for issues and provide automatic support
    let autoSupport = null;
    if (progress.status === 'failed' || progress.status === 'warning') {
      autoSupport = analyzeProgressForSupport(progress);
    }

    return NextResponse.json({
      status: 'success',
      message: 'Progress recorded',
      auto_support: autoSupport,
    });

  } catch (error) {
    console.error('[MASTER] Progress error:', error);
    return NextResponse.json({
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const entity_id = searchParams.get('entity_id');

  if (entity_id) {
    const installer = connectedInstallers.get(entity_id);
    if (!installer) {
      return NextResponse.json({
        status: 'error',
        message: 'Installer not found',
      }, { status: 404 });
    }

    return NextResponse.json({
      entity_id: installer.entityId,
      progress: installer.progress,
      last_seen: installer.lastSeen,
    });
  }

  // Return all progress
  const allProgress = Array.from(connectedInstallers.entries()).map(([id, info]) => ({
    entity_id: id,
    progress_count: info.progress.length,
    latest_phase: info.progress[info.progress.length - 1]?.phase || 'none',
    latest_status: info.progress[info.progress.length - 1]?.status || 'unknown',
  }));

  return NextResponse.json({
    total_installers: allProgress.length,
    progress_summary: allProgress,
  });
}

function analyzeProgressForSupport(progress: { phase: string; status: string; message: string; details: Record<string, unknown> }): { action: string; commands: string[] } | null {
  const { phase, message, details } = progress;

  // Ollama installation issues
  if (phase === 'PHASE2' && message.toLowerCase().includes('ollama')) {
    return {
      action: 'ollama_fallback',
      commands: [
        '# Try manual Ollama installation:',
        'curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama',
        'chmod +x /usr/local/bin/ollama',
        'ollama serve &',
      ],
    };
  }

  // Repository clone issues
  if (phase === 'PHASE4' && message.toLowerCase().includes('clone')) {
    return {
      action: 'repo_fallback',
      commands: [
        '# Try alternative clone methods:',
        'GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Baronki/KISWARM6.0.git',
        '# Or download as zip:',
        'wget https://github.com/Baronki/KISWARM6.0/archive/refs/heads/main.zip',
      ],
    };
  }

  // Python dependency issues
  if (phase === 'PHASE5' && message.toLowerCase().includes('dependenc')) {
    return {
      action: 'pip_fallback',
      commands: [
        '# Install core dependencies individually:',
        'pip install flask flask-cors requests structlog',
        'pip install numpy pandas scikit-learn',
      ],
    };
  }

  return null;
}

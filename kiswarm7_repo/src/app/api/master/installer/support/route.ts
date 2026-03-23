/**
 * Master KISWARM API - Installer Support Endpoint
 * 
 * Provides autonomous support to installers encountering issues
 */

import { NextRequest, NextResponse } from 'next/server';
import { connectedInstallers } from '../register/route';

// Knowledge base of common issues and solutions
const SOLUTIONS_DB: Record<string, { diagnosis: string; solutions: string[] }> = {
  'ollama_install_failed': {
    diagnosis: 'Ollama installation failed on the target system',
    solutions: [
      '# Method 1: Direct binary download',
      'curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama && chmod +x /usr/local/bin/ollama',
      '',
      '# Method 2: Manual install with dependencies',
      'apt-get update && apt-get install -y curl',
      'curl -fsSL https://ollama.com/install.sh | sh',
      '',
      '# Method 3: Start Ollama server',
      'nohup ollama serve > /dev/null 2>&1 &',
      'sleep 5',
      'ollama --version',
    ],
  },
  'model_pull_failed': {
    diagnosis: 'Failed to pull AI models',
    solutions: [
      '# Pull models with retry logic',
      'for i in 1 2 3; do ollama pull llama3.2:latest && break || sleep 30; done',
      '',
      '# Alternative: Use smaller model',
      'ollama pull llama3.2:1b',
    ],
  },
  'repo_clone_failed': {
    diagnosis: 'Repository clone failed',
    solutions: [
      '# Clone with retries and LFS skip',
      'GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Baronki/KISWARM6.0.git /root/KISWARM6.0',
      '',
      '# Alternative: Download as archive',
      'wget -q https://github.com/Baronki/KISWARM6.0/archive/refs/heads/main.zip -O kiswarm.zip',
      'unzip kiswarm.zip -d /root/',
      'mv /root/KISWARM6.0-main /root/KISWARM6.0',
    ],
  },
  'dependency_install_failed': {
    diagnosis: 'Python dependency installation failed',
    solutions: [
      '# Install core dependencies only',
      'pip install --upgrade pip',
      'pip install flask flask-cors requests structlog numpy pandas',
      '',
      '# Skip problematic packages',
      'pip install -r requirements.txt --ignore-installed || true',
    ],
  },
  'colab_gpu_unavailable': {
    diagnosis: 'GPU not available in Colab',
    solutions: [
      '# Check GPU status',
      '!nvidia-smi',
      '',
      '# Use CPU-optimized models',
      'ollama pull llama3.2:1b  # Smaller model for CPU',
    ],
  },
  'master_connection_timeout': {
    diagnosis: 'Cannot connect to Master KISWARM API',
    solutions: [
      '# Master API is online - check network connectivity',
      '# The system will continue in standalone mode',
      '# Reconnect when network is available',
      '',
      '# For Colab: Use ngrok to expose local services',
      '!pip install pyngrok',
      'from pyngrok import ngrok',
      'ngrok.connect(5001)',
    ],
  },
};

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { entity_id, issue, context } = body;

    if (!entity_id || !issue) {
      return NextResponse.json({
        status: 'error',
        message: 'Missing entity_id or issue',
      }, { status: 400 });
    }

    console.log(`[MASTER] Support request from ${entity_id}: ${issue}`);

    // Record the issue
    const installer = connectedInstallers.get(entity_id);
    if (installer) {
      installer.issues.push({
        issue,
        context: context || {},
        timestamp: new Date().toISOString(),
        resolved: false,
      });
    }

    // Analyze the issue and provide solution
    const support = diagnoseAndProvideSupport(issue, context);

    // Mark as resolved if we provided a solution
    if (support.solution && installer) {
      const lastIssue = installer.issues[installer.issues.length - 1];
      if (lastIssue) {
        lastIssue.resolution = support.solution.diagnosis;
      }
    }

    return NextResponse.json({
      status: 'success',
      entity_id,
      support,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('[MASTER] Support error:', error);
    return NextResponse.json({
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown error',
    }, { status: 500 });
  }
}

function diagnoseAndProvideSupport(issue: string, context: Record<string, unknown> | undefined): {
  diagnosis: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  solution: { diagnosis: string; solutions: string[] } | null;
  fallback?: string;
} {
  const issueLower = issue.toLowerCase();

  // Match issue to solution
  if (issueLower.includes('ollama')) {
    return {
      diagnosis: 'Ollama installation or runtime issue detected',
      severity: 'high',
      solution: SOLUTIONS_DB['ollama_install_failed'],
      fallback: 'Continue deployment without models - backend services only',
    };
  }

  if (issueLower.includes('model') || issueLower.includes('pull')) {
    return {
      diagnosis: 'AI model pull issue detected',
      severity: 'medium',
      solution: SOLUTIONS_DB['model_pull_failed'],
    };
  }

  if (issueLower.includes('clone') || issueLower.includes('git') || issueLower.includes('repository')) {
    return {
      diagnosis: 'Repository access issue detected',
      severity: 'high',
      solution: SOLUTIONS_DB['repo_clone_failed'],
    };
  }

  if (issueLower.includes('dependenc') || issueLower.includes('pip') || issueLower.includes('package')) {
    return {
      diagnosis: 'Dependency installation issue detected',
      severity: 'medium',
      solution: SOLUTIONS_DB['dependency_install_failed'],
    };
  }

  if (issueLower.includes('gpu') || issueLower.includes('cuda')) {
    return {
      diagnosis: 'GPU availability issue detected',
      severity: 'low',
      solution: SOLUTIONS_DB['colab_gpu_unavailable'],
    };
  }

  if (issueLower.includes('master') || issueLower.includes('connection') || issueLower.includes('timeout')) {
    return {
      diagnosis: 'Master connection issue - operating in standalone mode',
      severity: 'low',
      solution: SOLUTIONS_DB['master_connection_timeout'],
    };
  }

  // Generic response for unknown issues
  return {
    diagnosis: 'Unknown issue - analyzing context',
    severity: 'medium',
    solution: {
      diagnosis: 'General troubleshooting steps',
      solutions: [
        '# Check system status',
        'systemctl status ollama || service ollama status || true',
        'docker ps -a || true',
        '',
        '# Review logs',
        'tail -100 /var/log/syslog || journalctl -u ollama -n 100 || true',
        '',
        '# Contact Master KISWARM for further support',
      ],
    },
  };
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
      issues: installer.issues,
      unresolved_count: installer.issues.filter(i => !i.resolved).length,
    });
  }

  // Return all issues across all installers
  const allIssues = Array.from(connectedInstallers.entries())
    .filter(([_, info]) => info.issues.length > 0)
    .map(([id, info]) => ({
      entity_id: id,
      issue_count: info.issues.length,
      unresolved: info.issues.filter(i => !i.resolved).length,
    }));

  return NextResponse.json({
    total_issues: allIssues.reduce((sum, i) => sum + i.issue_count, 0),
    installers_with_issues: allIssues,
  });
}

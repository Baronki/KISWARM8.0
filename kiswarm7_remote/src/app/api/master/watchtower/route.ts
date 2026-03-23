/**
 * Master KISWARM API - Watchtower Guard Endpoint
 * 
 * 24/7 Autonomous monitoring system for KISWARM installers
 * - Detects new installers coming online
 * - Monitors deployment progress
 * - Provides automatic support and intervention
 * - Tracks swarm health metrics
 */

import { NextRequest, NextResponse } from 'next/server';
import { connectedInstallers, MASTER_ID } from '../installer/register/route';

// Watchtower state
interface WatchtowerState {
  startTime: string;
  uptime: number;
  totalDetected: number;
  totalSupported: number;
  activeConnections: number;
  alerts: Alert[];
  metrics: Metrics;
}

interface Alert {
  id: string;
  type: 'new_installer' | 'deployment_issue' | 'offline' | 'critical';
  entity_id: string;
  message: string;
  timestamp: string;
  handled: boolean;
}

interface Metrics {
  avgDeploymentTime: number;
  successRate: number;
  issuesPerInstaller: number;
  environments: Record<string, number>;
}

// In-memory state (use database in production)
let watchtowerState: WatchtowerState = {
  startTime: new Date().toISOString(),
  uptime: 0,
  totalDetected: 0,
  totalSupported: 0,
  activeConnections: 0,
  alerts: [],
  metrics: {
    avgDeploymentTime: 0,
    successRate: 0,
    issuesPerInstaller: 0,
    environments: {},
  },
};

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');

  // Update state
  updateWatchtowerState();

  switch (action) {
    case 'status':
      return getStatus();
    case 'alerts':
      return getAlerts();
    case 'metrics':
      return getMetrics();
    case 'intervention':
      return getInterventionQueue();
    default:
      return getFullReport();
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, data } = body;

    switch (action) {
      case 'alert':
        return handleAlert(data);
      case 'resolve_alert':
        return resolveAlert(body.alert_id);
      case 'intervention':
        return requestIntervention(data);
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

function updateWatchtowerState() {
  const now = Date.now();
  const startTime = new Date(watchtowerState.startTime).getTime();
  
  watchtowerState.uptime = Math.floor((now - startTime) / 1000);
  watchtowerState.activeConnections = connectedInstallers.size;
  
  // Update environment metrics
  const environments: Record<string, number> = {};
  for (const [_, installer] of connectedInstallers) {
    const env = installer.identity.environment || 'unknown';
    environments[env] = (environments[env] || 0) + 1;
  }
  watchtowerState.metrics.environments = environments;
  
  // Calculate success rate
  let totalProgress = 0;
  let successProgress = 0;
  let totalIssues = 0;
  
  for (const [_, installer] of connectedInstallers) {
    totalProgress += installer.progress.length;
    successProgress += installer.progress.filter(p => p.status === 'success').length;
    totalIssues += installer.issues.length;
  }
  
  if (totalProgress > 0) {
    watchtowerState.metrics.successRate = (successProgress / totalProgress) * 100;
  }
  
  if (connectedInstallers.size > 0) {
    watchtowerState.metrics.issuesPerInstaller = totalIssues / connectedInstallers.size;
  }
}

function getStatus(): Response {
  return NextResponse.json({
    status: 'OPERATIONAL',
    master_id: MASTER_ID,
    uptime_seconds: watchtowerState.uptime,
    uptime_human: formatUptime(watchtowerState.uptime),
    active_connections: watchtowerState.activeConnections,
    total_detected: watchtowerState.totalDetected,
    total_supported: watchtowerState.totalSupported,
    pending_alerts: watchtowerState.alerts.filter(a => !a.handled).length,
  });
}

function getAlerts(): Response {
  const pending = watchtowerState.alerts.filter(a => !a.handled);
  const recent = watchtowerState.alerts.slice(-20);
  
  return NextResponse.json({
    total_alerts: watchtowerState.alerts.length,
    pending_count: pending.length,
    pending: pending,
    recent: recent,
  });
}

function getMetrics(): Response {
  return NextResponse.json({
    uptime_seconds: watchtowerState.uptime,
    metrics: watchtowerState.metrics,
    environments: watchtowerState.metrics.environments,
  });
}

function getInterventionQueue(): Response {
  // Find installers that need intervention
  const needsIntervention = [];
  
  for (const [id, installer] of connectedInstallers) {
    // Check for failed phases
    const failedPhases = installer.progress.filter(p => p.status === 'failed');
    if (failedPhases.length > 0) {
      needsIntervention.push({
        entity_id: id,
        reason: 'failed_phases',
        failed_count: failedPhases.length,
        last_failure: failedPhases[failedPhases.length - 1],
      });
    }
    
    // Check for unresolved issues
    const unresolvedIssues = installer.issues.filter(i => !i.resolved);
    if (unresolvedIssues.length > 3) {
      needsIntervention.push({
        entity_id: id,
        reason: 'multiple_unresolved_issues',
        issue_count: unresolvedIssues.length,
      });
    }
    
    // Check for stale installers
    const lastSeen = new Date(installer.lastSeen).getTime();
    const minutesSinceSeen = (Date.now() - lastSeen) / 60000;
    if (minutesSinceSeen > 10 && installer.progress.length > 0) {
      const lastPhase = installer.progress[installer.progress.length - 1];
      if (lastPhase && lastPhase.status !== 'success') {
        needsIntervention.push({
          entity_id: id,
          reason: 'stale_deployment',
          minutes_offline: Math.floor(minutesSinceSeen),
          last_phase: lastPhase.phase,
        });
      }
    }
  }
  
  return NextResponse.json({
    intervention_count: needsIntervention.length,
    queue: needsIntervention,
  });
}

function getFullReport(): Response {
  return NextResponse.json({
    watchtower: watchtowerState,
    installers: Array.from(connectedInstallers.values()).map(i => ({
      entity_id: i.entityId,
      environment: i.identity.environment,
      hostname: i.identity.hostname,
      status: i.status,
      registered_at: i.registeredAt,
      last_seen: i.lastSeen,
      progress_count: i.progress.length,
      issue_count: i.issues.length,
      unresolved_issues: i.issues.filter(issue => !issue.resolved).length,
    })),
  });
}

function handleAlert(data: { type: string; entity_id: string; message: string }): Response {
  const alert: Alert = {
    id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    type: data.type as Alert['type'],
    entity_id: data.entity_id,
    message: data.message,
    timestamp: new Date().toISOString(),
    handled: false,
  };
  
  watchtowerState.alerts.push(alert);
  
  // Auto-handle certain alert types
  if (data.type === 'new_installer') {
    watchtowerState.totalDetected++;
    // Mark as handled immediately - registration already processed
    alert.handled = true;
  }
  
  console.log(`[WATCHTOWER] Alert: ${alert.type} from ${alert.entity_id}`);
  
  return NextResponse.json({
    status: 'success',
    alert_id: alert.id,
    handled: alert.handled,
  });
}

function resolveAlert(alert_id: string): Response {
  const alert = watchtowerState.alerts.find(a => a.id === alert_id);
  
  if (!alert) {
    return NextResponse.json({
      status: 'error',
      message: 'Alert not found',
    }, { status: 404 });
  }
  
  alert.handled = true;
  watchtowerState.totalSupported++;
  
  return NextResponse.json({
    status: 'success',
    message: 'Alert resolved',
    alert_id,
  });
}

function requestIntervention(data: { entity_id: string; action: string }): Response {
  const installer = connectedInstallers.get(data.entity_id);
  
  if (!installer) {
    return NextResponse.json({
      status: 'error',
      message: 'Installer not found',
    }, { status: 404 });
  }
  
  // Add intervention alert
  const alert: Alert = {
    id: `intervention_${Date.now()}`,
    type: 'critical',
    entity_id: data.entity_id,
    message: `Intervention requested: ${data.action}`,
    timestamp: new Date().toISOString(),
    handled: false,
  };
  
  watchtowerState.alerts.push(alert);
  
  console.log(`[WATCHTOWER] Intervention requested for ${data.entity_id}: ${data.action}`);
  
  return NextResponse.json({
    status: 'success',
    message: 'Intervention queued',
    alert_id: alert.id,
    recommended_actions: getInterventionActions(data.action, installer),
  });
}

function getInterventionActions(action: string, installer: { progress: { phase: string; status: string }[]; issues: { issue: string }[] }): string[] {
  const lastPhase = installer.progress[installer.progress.length - 1];
  
  switch (action) {
    case 'ollama_failed':
      return [
        'curl -L https://ollama.com/download/ollama-linux-amd64 -o /usr/local/bin/ollama',
        'chmod +x /usr/local/bin/ollama',
        'nohup ollama serve > /dev/null 2>&1 &',
      ];
    case 'clone_failed':
      return [
        'GIT_LFS_SKIP_SMUDGE=1 git clone --depth 1 https://github.com/Baronki/KISWARM6.0.git /root/KISWARM6.0',
      ];
    case 'connection_failed':
      return [
        '# Master is online - check network',
        '# Operating in standalone mode',
      ];
    default:
      return [
        '# Check logs',
        'tail -100 /var/log/syslog',
        '# Restart deployment',
        'python autonomous_kiswarm_installer.py --standalone',
      ];
  }
}

function formatUptime(seconds: number): string {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  const parts: string[] = [];
  if (days > 0) parts.push(`${days}d`);
  if (hours > 0) parts.push(`${hours}h`);
  if (minutes > 0) parts.push(`${minutes}m`);
  
  return parts.join(' ') || '< 1m';
}

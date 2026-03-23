'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

interface Installer {
  entity_id: string
  environment: string
  hostname: string
  status: 'active' | 'idle' | 'offline'
  registered_at: string
  last_seen: string
  progress_count: number
  issue_count: number
  unresolved_issues: number
}

interface WatchtowerStatus {
  status: string
  master_id: string
  uptime_seconds: number
  uptime_human: string
  active_connections: number
  total_detected: number
  total_supported: number
  pending_alerts: number
}

interface Alert {
  id: string
  type: string
  entity_id: string
  message: string
  timestamp: string
  handled: boolean
}

interface Metrics {
  avgDeploymentTime: number
  successRate: number
  issuesPerInstaller: number
  environments: Record<string, number>
}

export default function Home() {
  const [installers, setInstallers] = useState<Installer[]>([])
  const [watchtower, setWatchtower] = useState<WatchtowerStatus | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedInstaller, setSelectedInstaller] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      // Fetch installers
      const installersRes = await fetch('/api/master/installer/register')
      const installersData = await installersRes.json()
      
      // Fetch watchtower status
      const watchtowerRes = await fetch('/api/master/watchtower?action=status')
      const watchtowerData = await watchtowerRes.json()
      
      // Fetch alerts
      const alertsRes = await fetch('/api/master/watchtower?action=alerts')
      const alertsData = await alertsRes.json()
      
      // Fetch metrics
      const metricsRes = await fetch('/api/master/watchtower?action=metrics')
      const metricsData = await metricsRes.json()

      if (installersData.installers) {
        setInstallers(installersData.installers)
      }
      setWatchtower(watchtowerData)
      setAlerts(alertsData.pending || [])
      setMetrics(metricsData.metrics)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch data:', error)
      setLoading(false)
    }
  }, [])

  const hasLoadedRef = useRef(false)

  useEffect(() => {
    const intervalId = autoRefresh ? setInterval(fetchData, 5000) : null
    
    // Initial data fetch on component mount
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true
      // eslint-disable-next-line react-hooks/set-state-in-effect
      void fetchData()
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId)
    }
  }, [fetchData, autoRefresh])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return '#22c55e'
      case 'idle': return '#eab308'
      case 'offline': return '#ef4444'
      default: return '#6b7280'
    }
  }

  const getAlertTypeColor = (type: string) => {
    switch (type) {
      case 'new_installer': return '#3b82f6'
      case 'deployment_issue': return '#f59e0b'
      case 'offline': return '#6b7280'
      case 'critical': return '#ef4444'
      default: return '#6b7280'
    }
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#0a0a0a',
        color: '#fff'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '48px',
            height: '48px',
            border: '3px solid #333',
            borderTop: '3px solid #3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p>Initializing Master KISWARM...</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a0a',
      color: '#fff',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <header style={{
        borderBottom: '1px solid #222',
        padding: '16px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '20px'
          }}>
            🔱
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 'bold' }}>
              Master KISWARM Control Panel
            </h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#666' }}>
              v6.3.0 SEVENTY_FIVE_COMPLETE
            </p>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              style={{ width: '16px', height: '16px' }}
            />
            <span style={{ fontSize: '14px', color: '#888' }}>Auto-refresh</span>
          </label>
          
          <button
            onClick={fetchData}
            style={{
              padding: '8px 16px',
              backgroundColor: '#3b82f6',
              border: 'none',
              borderRadius: '6px',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Refresh
          </button>
        </div>
      </header>

      <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
        {/* Watchtower Status */}
        <section style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', marginBottom: '16px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>
            🗼 Watchtower Guard Status
          </h2>
          
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px'
          }}>
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>Status</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#22c55e' }}>
                {watchtower?.status || 'UNKNOWN'}
              </div>
            </div>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>Uptime</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold' }}>
                {watchtower?.uptime_human || '0m'}
              </div>
            </div>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>Active Installers</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#3b82f6' }}>
                {watchtower?.active_connections || 0}
              </div>
            </div>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>Total Detected</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#8b5cf6' }}>
                {watchtower?.total_detected || 0}
              </div>
            </div>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>Pending Alerts</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: alerts.length > 0 ? '#f59e0b' : '#22c55e' }}>
                {watchtower?.pending_alerts || 0}
              </div>
            </div>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ fontSize: '12px', color: '#666', marginBottom: '8px' }}>Success Rate</div>
              <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#22c55e' }}>
                {metrics?.successRate?.toFixed(1) || '0'}%
              </div>
            </div>
          </div>
        </section>

        {/* Alerts */}
        {alerts.length > 0 && (
          <section style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', marginBottom: '16px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>
              🚨 Active Alerts
            </h2>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              {alerts.map((alert, index) => (
                <div
                  key={alert.id}
                  style={{
                    padding: '12px 16px',
                    borderBottom: index < alerts.length - 1 ? '1px solid #222' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px'
                  }}
                >
                  <div style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: getAlertTypeColor(alert.type)
                  }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>
                      {alert.message}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {alert.entity_id} • {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <span style={{
                    padding: '4px 8px',
                    backgroundColor: getAlertTypeColor(alert.type) + '20',
                    color: getAlertTypeColor(alert.type),
                    borderRadius: '4px',
                    fontSize: '12px'
                  }}>
                    {alert.type}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Connected Installers */}
        <section style={{ marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', marginBottom: '16px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>
            🔌 Connected Installers
          </h2>
          
          {installers.length === 0 ? (
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '32px',
              textAlign: 'center',
              color: '#666'
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>📡</div>
              <p style={{ fontSize: '16px', marginBottom: '8px' }}>No installers connected</p>
              <p style={{ fontSize: '14px' }}>
                Waiting for KISWARM installers to come online...
              </p>
              <p style={{ fontSize: '12px', marginTop: '16px', color: '#444' }}>
                Master API: {watchtower?.master_id}
              </p>
            </div>
          ) : (
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              overflow: 'hidden'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#0a0a0a' }}>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: 'normal' }}>Entity ID</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: 'normal' }}>Environment</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: 'normal' }}>Status</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: 'normal' }}>Progress</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: 'normal' }}>Issues</th>
                    <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#666', fontWeight: 'normal' }}>Last Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {installers.map((installer, index) => (
                    <tr
                      key={installer.entity_id}
                      style={{
                        backgroundColor: selectedInstaller === installer.entity_id ? '#1a1a2e' : 'transparent',
                        cursor: 'pointer',
                        borderBottom: index < installers.length - 1 ? '1px solid #222' : 'none'
                      }}
                      onClick={() => setSelectedInstaller(
                        selectedInstaller === installer.entity_id ? null : installer.entity_id
                      )}
                    >
                      <td style={{ padding: '12px 16px', fontSize: '14px', fontFamily: 'monospace' }}>
                        {installer.entity_id.substring(0, 24)}...
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: '14px' }}>
                        {installer.environment || 'unknown'}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '4px 8px',
                          backgroundColor: getStatusColor(installer.status) + '20',
                          color: getStatusColor(installer.status),
                          borderRadius: '4px',
                          fontSize: '12px'
                        }}>
                          <span style={{
                            width: '6px',
                            height: '6px',
                            borderRadius: '50%',
                            backgroundColor: getStatusColor(installer.status)
                          }} />
                          {installer.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: '14px' }}>
                        {installer.progress_count} updates
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: '14px' }}>
                        {installer.unresolved_issues > 0 ? (
                          <span style={{ color: '#f59e0b' }}>
                            {installer.unresolved_issues} unresolved
                          </span>
                        ) : (
                          <span style={{ color: '#22c55e' }}>OK</span>
                        )}
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: '14px', color: '#666' }}>
                        {installer.last_seen ? new Date(installer.last_seen).toLocaleTimeString() : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Environments Distribution */}
        {metrics?.environments && Object.keys(metrics.environments).length > 0 && (
          <section style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', marginBottom: '16px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>
              🌍 Environments
            </h2>
            
            <div style={{
              backgroundColor: '#111',
              border: '1px solid #222',
              borderRadius: '8px',
              padding: '16px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '12px'
            }}>
              {Object.entries(metrics.environments).map(([env, count]) => (
                <div
                  key={env}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#1a1a2e',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                >
                  <span style={{ fontSize: '14px' }}>{env}</span>
                  <span style={{
                    padding: '2px 6px',
                    backgroundColor: '#3b82f6',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold'
                  }}>
                    {count}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Deployment Command */}
        <section>
          <h2 style={{ fontSize: '16px', marginBottom: '16px', color: '#888', textTransform: 'uppercase', letterSpacing: '1px' }}>
            📋 Single Command Deployment
          </h2>
          
          <div style={{
            backgroundColor: '#111',
            border: '1px solid #222',
            borderRadius: '8px',
            padding: '16px',
            fontFamily: 'monospace',
            fontSize: '13px',
            lineHeight: '1.6',
            overflow: 'auto'
          }}>
            <pre style={{ margin: 0, color: '#888' }}>
{`# KISWARM Autonomous Deployment (Copy to Colab/Gemini CLI)

# 1. Download installer
!curl -fsSL https://raw.githubusercontent.com/Baronki/KISWARM6.0/main/kiinstaller/autonomous_kiswarm_installer.py -o autonomous_kiswarm_installer.py

# 2. Install dependencies
!pip install -q flask flask-cors structlog requests pyngrok

# 3. Deploy (Master API will auto-detect)
from autonomous_kiswarm_installer import autonomous_deploy
result = autonomous_deploy(
    master_url="${typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'}"
)`}
            </pre>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid #222',
        padding: '16px 24px',
        textAlign: 'center',
        color: '#444',
        fontSize: '12px'
      }}>
        Master KISWARM API v6.3.0 • Watchtower Guard Active • {watchtower?.master_id}
      </footer>

      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

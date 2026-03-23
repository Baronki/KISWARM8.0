import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrendingUp, AlertCircle, CheckCircle, Activity, Users, DollarSign, Package, Zap } from "lucide-react";
import { useState, useEffect } from "react";
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { analyticsService, type AnalyticsDashboard as AnalyticsDashboardData } from "@/lib/analytics-service";

/**
 * Analytics Dashboard
 * Real-time metrics for investment trends, compliance monitoring, and KI-entity statistics
 */

export default function AnalyticsDashboard() {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(5000);

  useEffect(() => {
    // Initial load
    setData(analyticsService.generateAnalyticsData());

    // Auto-refresh
    const interval = setInterval(() => {
      setData(analyticsService.generateAnalyticsData());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [refreshInterval]);

  if (!data) return <div className="min-h-screen bg-background flex items-center justify-center">Loading...</div>;

  const kpis = analyticsService.calculateKPIs(data);
  const alerts = analyticsService.getComplianceAlerts(data);
  const insights = analyticsService.getInvestmentInsights(data);
  const health = analyticsService.getSystemHealth(data);

  const investmentColors = ['#00d9ff', '#ff006e', '#00ff88', '#ffd700', '#ff6b6b'];
  const investmentData = Object.entries(data.investments.investmentsByType).map(([name, value], idx) => ({
    name,
    value,
    color: investmentColors[idx % investmentColors.length],
  }));

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-4xl md:text-5xl font-mono font-bold glow-cyan">Analytics Dashboard</h1>
              <p className="text-muted-foreground mt-2">Real-time metrics for investment trends, compliance & KI-entity statistics</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Last Updated</p>
              <p className="font-mono text-cyan-300">{new Date(data.timestamp).toLocaleTimeString()}</p>
            </div>
          </div>

          {/* Refresh Controls */}
          <div className="flex gap-2">
            <Button
              onClick={() => setRefreshInterval(5000)}
              variant={refreshInterval === 5000 ? "default" : "outline"}
              className="font-mono text-xs"
            >
              5s
            </Button>
            <Button
              onClick={() => setRefreshInterval(10000)}
              variant={refreshInterval === 10000 ? "default" : "outline"}
              className="font-mono text-xs"
            >
              10s
            </Button>
            <Button
              onClick={() => setRefreshInterval(30000)}
              variant={refreshInterval === 30000 ? "default" : "outline"}
              className="font-mono text-xs"
            >
              30s
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        {/* Alerts Section */}
        {alerts.length > 0 && (
          <div className="mb-8 space-y-2">
            {alerts.map((alert, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-lg border flex items-center gap-3 ${
                  alert.level === 'critical'
                    ? 'bg-red-500/10 border-red-500/30'
                    : 'bg-yellow-500/10 border-yellow-500/30'
                }`}
              >
                {alert.level === 'critical' ? (
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                )}
                <span className={`font-mono text-sm ${alert.level === 'critical' ? 'text-red-300' : 'text-yellow-300'}`}>
                  {alert.message}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* KPI Cards */}
        <div className="grid md:grid-cols-3 gap-4 mb-12">
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-mono">Investment Growth</p>
                <p className="text-3xl font-mono font-bold text-cyan-300 mt-2">{kpis.investmentGrowth}%</p>
              </div>
              <TrendingUp className="w-8 h-8 text-cyan-400" />
            </div>
          </Card>

          <Card className="bg-card border-green-500/30 neon-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-mono">Compliance Score</p>
                <p className="text-3xl font-mono font-bold text-green-300 mt-2">{kpis.complianceScore}%</p>
              </div>
              <CheckCircle className="w-8 h-8 text-green-400" />
            </div>
          </Card>

          <Card className="bg-card border-magenta-500/30 neon-border p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground font-mono">Active Entities</p>
                <p className="text-3xl font-mono font-bold text-magenta-300 mt-2">{data.kiEntities.activeEntities.toLocaleString()}</p>
              </div>
              <Users className="w-8 h-8 text-magenta-400" />
            </div>
          </Card>
        </div>

        {/* System Health */}
        <div className="grid md:grid-cols-4 gap-4 mb-12">
          <Card className="bg-card border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">System Status</p>
            <p className="font-mono font-bold text-cyan-300">{health.status}</p>
            <p className="text-xs text-muted-foreground mt-2">Uptime: {health.uptime}%</p>
          </Card>
          <Card className="bg-card border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">Latency</p>
            <p className="font-mono font-bold text-cyan-300">{health.latency}</p>
            <p className="text-xs text-muted-foreground mt-2">Avg Response Time</p>
          </Card>
          <Card className="bg-card border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">Error Rate</p>
            <p className="font-mono font-bold text-green-300">{health.errorRate}</p>
            <p className="text-xs text-muted-foreground mt-2">System Errors</p>
          </Card>
          <Card className="bg-card border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">Transactions</p>
            <p className="font-mono font-bold text-magenta-300">{data.compliance.totalTransactions.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground mt-2">Total Processed</p>
          </Card>
        </div>

        {/* Charts Section */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {/* Investment Trend */}
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-cyan-300 mb-4">Investment Trend (30 Days)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.investments.investmentTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#00d9ff20" />
                <XAxis dataKey="date" stroke="#666" style={{ fontSize: '12px' }} />
                <YAxis stroke="#666" style={{ fontSize: '12px' }} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0e27', border: '1px solid #00d9ff' }} />
                <Line type="monotone" dataKey="amount" stroke="#00d9ff" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Compliance Trend */}
          <Card className="bg-card border-green-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-green-300 mb-4">Compliance Rate (30 Days)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.compliance.complianceTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#00ff8820" />
                <XAxis dataKey="date" stroke="#666" style={{ fontSize: '12px' }} />
                <YAxis stroke="#666" style={{ fontSize: '12px' }} domain={[95, 100]} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0e27', border: '1px solid #00ff88' }} />
                <Line type="monotone" dataKey="rate" stroke="#00ff88" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Investment by Type */}
          <Card className="bg-card border-magenta-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-magenta-300 mb-4">Investment Distribution</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={investmentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name.substring(0, 15)}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {investmentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>

          {/* TCS Orders Trend */}
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-cyan-300 mb-4">TCS Orders (30 Days)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.tcsOrders.orderTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#00d9ff20" />
                <XAxis dataKey="date" stroke="#666" style={{ fontSize: '12px' }} />
                <YAxis stroke="#666" style={{ fontSize: '12px' }} />
                <Tooltip contentStyle={{ backgroundColor: '#0a0e27', border: '1px solid #00d9ff' }} />
                <Bar dataKey="orders" fill="#00d9ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        {/* Detailed Metrics */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {/* Investment Metrics */}
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-cyan-300 mb-4">Investment Metrics</h3>
            <div className="space-y-3 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Investments</span>
                <span className="text-cyan-300">{data.investments.totalInvestments.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Invested</span>
                <span className="text-cyan-300">€{(data.investments.totalInvestedAmount / 1000000).toFixed(1)}M</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Avg Size</span>
                <span className="text-cyan-300">€{data.investments.averageInvestmentSize.toLocaleString()}</span>
              </div>
              <div className="border-t border-border pt-3 mt-3">
                <p className="text-muted-foreground mb-2">Top Product</p>
                <p className="text-cyan-300 text-xs">{insights.topInvestmentProduct}</p>
              </div>
            </div>
          </Card>

          {/* Compliance Metrics */}
          <Card className="bg-card border-green-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-green-300 mb-4">Compliance Metrics</h3>
            <div className="space-y-3 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Transactions</span>
                <span className="text-green-300">{data.compliance.totalTransactions.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Compliant</span>
                <span className="text-green-300">{data.compliance.compliantTransactions.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Rate</span>
                <span className="text-green-300">{data.compliance.complianceRate.toFixed(2)}%</span>
              </div>
              <div className="border-t border-border pt-3 mt-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">KYC Verified</span>
                  <span className="text-green-300">{data.compliance.kycVerifications.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </Card>

          {/* KI-Entity Metrics */}
          <Card className="bg-card border-magenta-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-magenta-300 mb-4">KI-Entity Metrics</h3>
            <div className="space-y-3 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Entities</span>
                <span className="text-magenta-300">{data.kiEntities.totalEntities.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Active</span>
                <span className="text-magenta-300">{data.kiEntities.activeEntities.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Verified</span>
                <span className="text-magenta-300">{data.kiEntities.verifiedEntities.toLocaleString()}</span>
              </div>
              <div className="border-t border-border pt-3 mt-3">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Avg Reputation</span>
                  <span className="text-magenta-300">{data.kiEntities.averageReputation.toFixed(1)}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Payment & Order Metrics */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Payment Metrics */}
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-cyan-300 mb-4">Payment Metrics</h3>
            <div className="space-y-3 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Deposits</span>
                <span className="text-cyan-300">{data.payments.totalDeposits.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Withdrawals</span>
                <span className="text-cyan-300">{data.payments.totalWithdrawals.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Net Flow</span>
                <span className="text-green-300">€{(data.payments.netFlow / 1000000).toFixed(1)}M</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Success Rate</span>
                <span className="text-green-300">{data.payments.paymentSuccessRate.toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Pending</span>
                <span className="text-yellow-300">{data.payments.pendingPayments}</span>
              </div>
            </div>
          </Card>

          {/* TCS Order Metrics */}
          <Card className="bg-card border-magenta-500/30 neon-border p-6">
            <h3 className="font-mono font-bold text-magenta-300 mb-4">TCS Order Metrics</h3>
            <div className="space-y-3 text-sm font-mono">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Orders</span>
                <span className="text-magenta-300">{data.tcsOrders.totalOrders.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Completed</span>
                <span className="text-green-300">{data.tcsOrders.completedOrders.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Pending</span>
                <span className="text-yellow-300">{data.tcsOrders.pendingOrders.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Value</span>
                <span className="text-magenta-300">€{(data.tcsOrders.totalOrderValue / 1000000).toFixed(1)}M</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Fulfillment Rate</span>
                <span className="text-green-300">{kpis.orderFulfillmentRate}%</span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

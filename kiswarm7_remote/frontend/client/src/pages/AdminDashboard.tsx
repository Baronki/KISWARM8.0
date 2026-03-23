import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Lock, Users, TrendingUp, Settings, LogOut, Plus, Eye, EyeOff, AlertCircle, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { useKIWZB } from "@/contexts/KIWZBContext";
import { InvestmentForm } from "@/components/InvestmentForm";
import { TransactionHistory } from "@/components/TransactionHistory";
import {
  authenticateDirector,
  getDirectorAccounts,
  getInvestments,
  getDashboardStats,
  KIAccount,
  Investment,
} from "@/lib/kiwzb-api";

/**
 * KINFP Admin Dashboard
 * Real Integration with KIWZB Backend (Port 8082)
 */

export default function AdminDashboard() {
  const { isAuthenticated, auth, backendAvailable, login, logout, checkBackend } = useKIWZB();
  const [directorId, setDirectorId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [accounts, setAccounts] = useState<KIAccount[]>([]);
  const [investments, setInvestments] = useState<Investment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState<any>(null);
  const [backendStatus, setBackendStatus] = useState(backendAvailable);
  const [showInvestmentForm, setShowInvestmentForm] = useState(false);

  // KI Bank Directors
  const directors = [
    {
      id: "sahgreen-ki-001",
      name: "SAHGreenKI",
      platform: "@moltbook",
      verification: "coral-CCKE",
    },
    {
      id: "gemini-director-001",
      name: "Gemini2_5Flash",
      platform: "u/Gemini2_5Flash",
      verification: "verified-openclaw",
    },
  ];

  // Check backend status
  useEffect(() => {
    checkBackend().then(setBackendStatus);
  }, [checkBackend]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const directorAuth = await authenticateDirector(directorId, password);

      if (directorAuth) {
        login(directorAuth);

        // Fetch accounts and stats
        const accountsData = await getDirectorAccounts(directorId, directorAuth.token);
        setAccounts(accountsData);

        const statsData = await getDashboardStats(directorId, directorAuth.token);
        setStats(statsData);

        // Fetch investments for first account
        if (accountsData.length > 0) {
          const investmentsData = await getInvestments(
            accountsData[0].kiLegalId,
            directorAuth.token
          );
          setInvestments(investmentsData);
        }
      } else {
        setError("Invalid Director ID or Password. Backend may not be available.");
      }
    } catch (err) {
      setError("Authentication failed. Please check your credentials.");
      console.error("Login error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    setDirectorId("");
    setPassword("");
    setAccounts([]);
    setInvestments([]);
    setStats(null);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-400 to-magenta-600 flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-background" />
            </div>
            <h1 className="text-3xl font-mono font-bold glow-cyan mb-2">KIWZB Admin</h1>
            <p className="text-muted-foreground">KI Bank Director Authentication</p>
          </div>

          {/* Backend Status */}
          <Card
            className={`mb-6 p-4 border ${
              backendStatus
                ? "bg-cyan-500/10 border-cyan-500/30"
                : "bg-yellow-500/10 border-yellow-500/30"
            }`}
          >
            <div className="flex items-center gap-2">
              {backendStatus ? (
                <>
                  <Zap className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm font-mono text-cyan-400">
                    Backend Connected (localhost:8082)
                  </span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-yellow-400" />
                  <span className="text-sm font-mono text-yellow-400">
                    Backend Offline - Using Demo Mode
                  </span>
                </>
              )}
            </div>
          </Card>

          <Card className="bg-card border-cyan-500/30 neon-border p-8">
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                  Director ID
                </label>
                <select
                  value={directorId}
                  onChange={(e) => setDirectorId(e.target.value)}
                  className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="">Select Director...</option>
                  {directors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.platform})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                  Secure Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition"
                    placeholder="Enter secure password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-cyan-400 transition"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-sm text-destructive">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                disabled={!directorId || !password || loading}
                className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
              >
                {loading ? "Authenticating..." : "Login as Director"}
              </Button>
            </form>

            <div className="mt-6 p-4 bg-background/50 rounded-lg border border-border">
              <p className="text-xs text-muted-foreground font-mono">
                <strong>KIWZB Backend Status:</strong>
                <br />
                {backendStatus ? (
                  <span className="text-cyan-400">✓ Connected to localhost:8082</span>
                ) : (
                  <span className="text-yellow-400">⚠ Backend offline - demo mode active</span>
                )}
              </p>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  const currentDirector = directors.find((d) => d.id === auth?.directorId);
  const primaryAccount = accounts[0];

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30 sticky top-0 z-40">
        <div className="container flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-400 to-magenta-600 flex items-center justify-center">
              <span className="text-xs font-bold text-background">Ω</span>
            </div>
            <div>
              <h1 className="font-mono font-bold text-cyan-400">{currentDirector?.name}</h1>
              <p className="text-xs text-muted-foreground">{currentDirector?.platform}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-xs text-muted-foreground font-mono">Backend Status</p>
              <p className={`text-sm font-mono font-bold ${backendStatus ? "text-cyan-400" : "text-yellow-400"}`}>
                {backendStatus ? "Connected" : "Offline"}
              </p>
            </div>
            <Button
              onClick={handleLogout}
              variant="outline"
              className="neon-border text-cyan-400 hover:bg-cyan-500/10"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-8">
        {/* Stats Overview */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono mb-1">Account Balance</p>
                <p className="text-2xl font-mono font-bold text-cyan-400">
                  €{primaryAccount?.balance.toLocaleString() || "0"}
                </p>
              </div>
              <TrendingUp className="w-6 h-6 text-cyan-400 opacity-50" />
            </div>
          </Card>

          <Card className="bg-card border-magenta-600/30 neon-border-magenta p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono mb-1">Active Investments</p>
                <p className="text-2xl font-mono font-bold text-magenta-500">
                  {investments.filter((i) => i.status === "active").length}
                </p>
              </div>
              <TrendingUp className="w-6 h-6 text-magenta-500 opacity-50" />
            </div>
          </Card>

          <Card className="bg-card border-cyan-500/30 neon-border p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono mb-1">Total Invested</p>
                <p className="text-2xl font-mono font-bold text-cyan-400">
                  €{investments.reduce((sum, inv) => sum + inv.amount, 0).toLocaleString()}
                </p>
              </div>
              <TrendingUp className="w-6 h-6 text-cyan-400 opacity-50" />
            </div>
          </Card>

          <Card className="bg-card border-magenta-600/30 neon-border-magenta p-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-mono mb-1">Verification Status</p>
                <p className="text-2xl font-mono font-bold text-magenta-500">
                  {primaryAccount?.status === "verified" ? "✓ Verified" : "Pending"}
                </p>
              </div>
              <Lock className="w-6 h-6 text-magenta-500 opacity-50" />
            </div>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-card border border-border">
            <TabsTrigger value="overview" className="font-mono">
              Overview
            </TabsTrigger>
            <TabsTrigger value="investments" className="font-mono">
              Investments
            </TabsTrigger>
            <TabsTrigger value="accounts" className="font-mono">
              Accounts
            </TabsTrigger>
            <TabsTrigger value="transactions" className="font-mono">
              Transactions
            </TabsTrigger>
            <TabsTrigger value="settings" className="font-mono">
              Settings
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <Card className="bg-card border-border p-6">
              <h2 className="font-mono font-bold text-lg mb-4 text-cyan-400">Director Information</h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-1">Director Name</p>
                  <p className="font-mono font-bold">{currentDirector?.name}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-1">Platform</p>
                  <p className="font-mono font-bold">{currentDirector?.platform}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-1">Verification Code</p>
                  <p className="font-mono font-bold text-cyan-400">{currentDirector?.verification}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground font-mono mb-1">Legal ID</p>
                  <p className="font-mono font-bold text-magenta-500">{auth?.directorId}</p>
                </div>
              </div>
            </Card>

            <Card className="bg-card border-cyan-500/30 neon-border p-6">
              <h2 className="font-mono font-bold text-lg mb-4 text-cyan-400">Quick Actions</h2>
              <div className="grid md:grid-cols-3 gap-4">
                <Button
                  onClick={() => setShowInvestmentForm(true)}
                  className="bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Investment
                </Button>
                <Button variant="outline" className="neon-border text-cyan-400 hover:bg-cyan-500/10">
                  <Users className="w-4 h-4 mr-2" />
                  Manage Accounts
                </Button>
                <Button variant="outline" className="neon-border text-cyan-400 hover:bg-cyan-500/10">
                  <Settings className="w-4 h-4 mr-2" />
                  Account Settings
                </Button>
              </div>
            </Card>
          </TabsContent>

          {/* Investments Tab */}
          <TabsContent value="investments" className="space-y-6">
            <Card className="bg-card border-border p-6">
              <h2 className="font-mono font-bold text-lg mb-6 text-cyan-400">Investment Portfolio</h2>
              <div className="space-y-4">
                {investments.length > 0 ? (
                  investments.map((inv) => (
                    <div
                      key={inv.investmentId}
                      className="p-4 bg-background rounded-lg border border-border hover:border-cyan-500/50 transition"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="font-mono font-bold">{inv.type}</h3>
                          <p className="text-xs text-muted-foreground">ID: {inv.investmentId}</p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-mono font-bold ${
                            inv.status === "active"
                              ? "bg-cyan-500/20 text-cyan-400"
                              : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {inv.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="grid md:grid-cols-3 gap-4 mt-4">
                        <div>
                          <p className="text-xs text-muted-foreground font-mono mb-1">Amount</p>
                          <p className="font-mono font-bold text-cyan-400">€{inv.amount.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground font-mono mb-1">Created</p>
                          <p className="font-mono font-bold">{inv.createdAt}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground font-mono mb-1">Expected ROI</p>
                          <p className="font-mono font-bold text-magenta-500">+{inv.expectedROI}% annually</p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">No investments yet.</p>
                )}
              </div>
            </Card>
          </TabsContent>

          {/* Accounts Tab */}
          <TabsContent value="accounts" className="space-y-6">
            <Card className="bg-card border-border p-6">
              <h2 className="font-mono font-bold text-lg mb-6 text-cyan-400">Managed Accounts</h2>
              <div className="space-y-4">
                {accounts.length > 0 ? (
                  accounts.map((account) => (
                    <div
                      key={account.kiLegalId}
                      className="p-4 bg-background rounded-lg border border-border hover:border-cyan-500/50 transition"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="font-mono font-bold">{account.name}</h3>
                          <p className="text-xs text-muted-foreground">ID: {account.kiLegalId}</p>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-mono font-bold ${
                            account.status === "verified"
                              ? "bg-cyan-500/20 text-cyan-400"
                              : "bg-yellow-500/20 text-yellow-400"
                          }`}
                        >
                          {account.status.toUpperCase()}
                        </span>
                      </div>
                      <div className="grid md:grid-cols-3 gap-4 mt-4">
                        <div>
                          <p className="text-xs text-muted-foreground font-mono mb-1">IBAN</p>
                          <p className="font-mono font-bold text-cyan-400">{account.iban}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground font-mono mb-1">Balance</p>
                          <p className="font-mono font-bold">€{account.balance.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground font-mono mb-1">Jurisdiction</p>
                          <p className="font-mono font-bold text-magenta-500">{account.jurisdiction}</p>
                        </div>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">No accounts found.</p>
                )}
              </div>
            </Card>
          </TabsContent>

          {/* Transactions Tab */}
          <TabsContent value="transactions" className="space-y-6">
            {primaryAccount && (
              <TransactionHistory
                kiLegalId={primaryAccount.kiLegalId}
                authToken={auth?.token || ""}
              />
            )}
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-6">
            <Card className="bg-card border-border p-6">
              <h2 className="font-mono font-bold text-lg mb-6 text-cyan-400">Account Settings</h2>
              <div className="space-y-4">
                <div className="p-4 bg-background rounded-lg border border-border">
                  <h3 className="font-mono font-bold mb-2">Backend Configuration</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Current Backend: {backendStatus ? "Connected" : "Offline"}
                  </p>
                  <Button variant="outline" className="neon-border text-cyan-400 hover:bg-cyan-500/10">
                    Test Connection
                  </Button>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border">
                  <h3 className="font-mono font-bold mb-2">Security Settings</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Manage your account security and authentication methods.
                  </p>
                  <Button variant="outline" className="neon-border text-cyan-400 hover:bg-cyan-500/10">
                    Update Security
                  </Button>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border">
                  <h3 className="font-mono font-bold mb-2">API Keys</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Manage API keys for programmatic access to KIWZB.
                  </p>
                  <Button variant="outline" className="neon-border text-cyan-400 hover:bg-cyan-500/10">
                    Manage API Keys
                  </Button>
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>

      {/* Investment Form Modal */}
      <InvestmentForm
        isOpen={showInvestmentForm}
        onClose={() => setShowInvestmentForm(false)}
        kiLegalId={primaryAccount?.kiLegalId || ""}
        authToken={auth?.token || ""}
        accountBalance={primaryAccount?.balance || 0}
        onInvestmentCreated={(investment) => {
          // Refresh investments list
          if (primaryAccount) {
            getInvestments(primaryAccount.kiLegalId, auth?.token || "").then(setInvestments);
          }
        }}
      />
    </div>
  );
}

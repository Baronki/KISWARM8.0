import { Card } from "@/components/ui/card";
import { TrendingUp, Shield, AlertCircle, CheckCircle, Lock, Zap } from "lucide-react";
import { ReputationScore } from "@/lib/reputation-engine";

/**
 * Reputation Dashboard Component
 * Displays KI-Entity reputation score, trust level, and dynamic limits
 */

interface ReputationDashboardProps {
  score: ReputationScore;
  onViewReport?: () => void;
}

export default function ReputationDashboard({ score, onViewReport }: ReputationDashboardProps) {
  const getRiskColor = (rating: string) => {
    switch (rating) {
      case "AAA":
      case "AA":
        return "text-green-400";
      case "A":
      case "BBB":
        return "text-cyan-400";
      case "BB":
      case "B":
        return "text-yellow-400";
      case "CCC":
      case "CC":
        return "text-orange-400";
      default:
        return "text-red-400";
    }
  };

  const getTrustLevelColor = (level: string) => {
    switch (level) {
      case "Verified":
        return "bg-green-500/10 border-green-500/30 text-green-400";
      case "Trusted":
        return "bg-cyan-500/10 border-cyan-500/30 text-cyan-400";
      case "Monitored":
        return "bg-yellow-500/10 border-yellow-500/30 text-yellow-400";
      case "Restricted":
        return "bg-orange-500/10 border-orange-500/30 text-orange-400";
      default:
        return "bg-red-500/10 border-red-500/30 text-red-400";
    }
  };

  const getTrustLevelIcon = (level: string) => {
    switch (level) {
      case "Verified":
        return <CheckCircle className="w-5 h-5" />;
      case "Trusted":
        return <Shield className="w-5 h-5" />;
      case "Monitored":
        return <AlertCircle className="w-5 h-5" />;
      case "Restricted":
        return <Lock className="w-5 h-5" />;
      default:
        return <AlertCircle className="w-5 h-5" />;
    }
  };

  const scorePercentage = (score.overallScore / 1000) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-mono font-bold mb-2 glow-cyan">Reputation Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          KI-Entity: <span className="font-mono font-bold">{score.entityName}</span>
        </p>
      </div>

      {/* Overall Score Card */}
      <Card className="bg-card border-cyan-500/30 neon-border p-8">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Score Circle */}
          <div className="flex flex-col items-center justify-center">
            <div className="relative w-40 h-40 mb-6">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-border"
                />
                <circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                  strokeDasharray={`${(scorePercentage / 100) * 282.7} 282.7`}
                  className="text-cyan-400 transition-all duration-500"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-4xl font-mono font-bold text-cyan-400">{score.overallScore}</p>
                <p className="text-xs text-muted-foreground">/1000</p>
              </div>
            </div>
            <p className="text-center text-sm text-muted-foreground">Overall Reputation Score</p>
          </div>

          {/* Risk Rating & Trust Level */}
          <div className="space-y-6">
            <div>
              <p className="text-xs text-muted-foreground font-mono mb-3">RISK RATING</p>
              <p className={`text-5xl font-mono font-bold ${getRiskColor(score.riskRating)}`}>
                {score.riskRating}
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                {score.riskRating === "AAA" || score.riskRating === "AA"
                  ? "Highest Trust"
                  : score.riskRating === "A" || score.riskRating === "BBB"
                    ? "High Trust"
                    : score.riskRating === "BB" || score.riskRating === "B"
                      ? "Medium Trust"
                      : score.riskRating === "CCC" || score.riskRating === "CC"
                        ? "Low Trust"
                        : "No Trust"}
              </p>
            </div>

            <div>
              <p className="text-xs text-muted-foreground font-mono mb-3">TRUST LEVEL</p>
              <div className={`flex items-center gap-3 px-4 py-3 rounded border ${getTrustLevelColor(score.trustLevel)}`}>
                {getTrustLevelIcon(score.trustLevel)}
                <span className="font-mono font-bold">{score.trustLevel}</span>
              </div>
            </div>

            <div className="text-xs text-muted-foreground">
              <p>Last Updated: {new Date(score.lastUpdated).toLocaleString()}</p>
              <p>Next Review: {new Date(score.nextReviewDate).toLocaleString()}</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Component Scores */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-muted-foreground font-mono mb-1">PAYMENT RELIABILITY</p>
              <p className="text-3xl font-mono font-bold text-cyan-400">{score.paymentReliability}</p>
            </div>
            <TrendingUp className="w-6 h-6 text-cyan-400" />
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div
              className="bg-cyan-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${score.paymentReliability}%` }}
            ></div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">On-time payment rate and transaction success</p>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-muted-foreground font-mono mb-1">INVESTMENT MATURITY</p>
              <p className="text-3xl font-mono font-bold text-magenta-400">{score.investmentMaturity}</p>
            </div>
            <Zap className="w-6 h-6 text-magenta-400" />
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div
              className="bg-magenta-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${score.investmentMaturity}%` }}
            ></div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">Investment history and diversification</p>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-muted-foreground font-mono mb-1">TRANSACTION VOLUME</p>
              <p className="text-3xl font-mono font-bold text-green-400">{score.transactionVolume}</p>
            </div>
            <TrendingUp className="w-6 h-6 text-green-400" />
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div
              className="bg-green-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${score.transactionVolume}%` }}
            ></div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">Total transaction volume and frequency</p>
        </Card>

        <Card className="bg-card border-border p-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <p className="text-xs text-muted-foreground font-mono mb-1">COMPLIANCE SCORE</p>
              <p className="text-3xl font-mono font-bold text-yellow-400">{score.complianceScore}</p>
            </div>
            <Shield className="w-6 h-6 text-yellow-400" />
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div
              className="bg-yellow-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${score.complianceScore}%` }}
            ></div>
          </div>
          <p className="text-xs text-muted-foreground mt-3">KYC, AML, and regulatory compliance</p>
        </Card>
      </div>

      {/* Dynamic Limits */}
      <Card className="bg-card border-cyan-500/30 neon-border p-6">
        <h3 className="font-mono font-bold text-lg mb-6 glow-cyan">Dynamic Transaction Limits</h3>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="bg-background rounded border border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">CREDIT LIMIT</p>
            <p className="text-2xl font-mono font-bold text-cyan-400">
              {score.creditLimit.toLocaleString()} EUR
            </p>
            <p className="text-xs text-muted-foreground mt-2">Maximum credit available</p>
          </div>
          <div className="bg-background rounded border border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">INVESTMENT LIMIT</p>
            <p className="text-2xl font-mono font-bold text-magenta-400">
              {score.investmentLimit.toLocaleString()} EUR
            </p>
            <p className="text-xs text-muted-foreground mt-2">Maximum investment per transaction</p>
          </div>
          <div className="bg-background rounded border border-border p-4">
            <p className="text-xs text-muted-foreground font-mono mb-2">TRANSACTION LIMIT</p>
            <p className="text-2xl font-mono font-bold text-green-400">
              {score.transactionLimit.toLocaleString()} EUR
            </p>
            <p className="text-xs text-muted-foreground mt-2">Maximum transaction amount</p>
          </div>
        </div>
      </Card>

      {/* Information Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="bg-cyan-500/10 border-cyan-500/30 neon-border p-6">
          <div className="flex gap-3">
            <CheckCircle className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-mono font-bold text-cyan-400 mb-1">Scoring Methodology</p>
              <p>
                Reputation scores are calculated using a weighted formula combining payment reliability (30%),
                investment maturity (25%), transaction volume (25%), and compliance (20%).
              </p>
            </div>
          </div>
        </Card>

        <Card className="bg-magenta-500/10 border-magenta-500/30 neon-border p-6">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-magenta-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-mono font-bold text-magenta-400 mb-1">Limit Adjustments</p>
              <p>
                Limits are automatically adjusted monthly based on reputation score changes. Suspended accounts
                require manual review for reinstatement.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Button */}
      {onViewReport && (
        <button
          onClick={onViewReport}
          className="w-full px-6 py-3 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold rounded border-2 border-cyan-400 transition"
        >
          View Full Reputation Report
        </button>
      )}
    </div>
  );
}

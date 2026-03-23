import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Download, RefreshCw, AlertCircle, CheckCircle, Eye } from "lucide-react";
import ReputationDashboard from "@/components/ReputationDashboard";
import {
  generateReputationScore,
  generateReputationReport,
  ReputationScore,
  TransactionMetrics,
  InvestmentMetrics,
  ComplianceRecord,
} from "@/lib/reputation-engine";

/**
 * Reputation Management Page
 * Complete reputation system management for KI Bank Directors
 */

export default function ReputationManagement() {
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);
  const [reputationScores, setReputationScores] = useState<Map<string, ReputationScore>>(new Map());
  const [showReport, setShowReport] = useState(false);

  // Mock KI entities for demonstration
  const mockEntities = [
    {
      id: "ki-001",
      name: "SAHGreenKI",
      verified: true,
    },
    {
      id: "ki-002",
      name: "Gemini2_5Flash",
      verified: true,
    },
    {
      id: "ki-003",
      name: "QuantumSwarm-AI",
      verified: false,
    },
    {
      id: "ki-004",
      name: "NeuralNet-Entity",
      verified: false,
    },
  ];

  // Generate mock metrics for demonstration
  const generateMockMetrics = (entityId: string) => {
    const baseValue = entityId.charCodeAt(5);

    const transactionMetrics: TransactionMetrics = {
      totalTransactions: 50 + baseValue * 2,
      successfulTransactions: 48 + baseValue * 2,
      failedTransactions: 2,
      totalVolume: 500000 + baseValue * 10000,
      averageTransactionSize: 10000 + baseValue * 200,
      onTimePaymentRate: 0.95 + (baseValue % 5) * 0.01,
      latePaymentCount: baseValue % 3,
      defaultCount: 0,
    };

    const investmentMetrics: InvestmentMetrics = {
      totalInvestments: 15 + baseValue,
      totalInvestedAmount: 250000 + baseValue * 5000,
      averageInvestmentSize: 16666 + baseValue * 300,
      investmentDiversification: 0.7 + (baseValue % 3) * 0.1,
      profitabilityScore: 0.3 + (baseValue % 7) * 0.05,
      riskTolerance: baseValue % 3 === 0 ? "low" : baseValue % 3 === 1 ? "medium" : "high",
    };

    const complianceRecords: ComplianceRecord[] = [
      {
        entityId,
        checkType: "kyc",
        status: "passed",
        timestamp: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        details: "KYC verification completed successfully",
      },
      {
        entityId,
        checkType: "aml",
        status: "passed",
        timestamp: new Date(Date.now() - 20 * 24 * 60 * 60 * 1000).toISOString(),
        details: "AML screening passed",
      },
      {
        entityId,
        checkType: "sanctions",
        status: "passed",
        timestamp: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        details: "Sanctions list check passed",
      },
    ];

    return { transactionMetrics, investmentMetrics, complianceRecords };
  };

  const calculateScore = (entityId: string, entityName: string) => {
    const { transactionMetrics, investmentMetrics, complianceRecords } = generateMockMetrics(entityId);
    const score = generateReputationScore(entityId, entityName, transactionMetrics, investmentMetrics, complianceRecords);
    setReputationScores(prev => new Map(prev).set(entityId, score));
    setSelectedEntity(entityId);
  };

  const getSelectedScore = () => {
    if (!selectedEntity) return null;
    return reputationScores.get(selectedEntity);
  };

  const downloadReport = (entityId: string) => {
    const score = reputationScores.get(entityId);
    if (!score) return;

    const report = generateReputationReport(score);
    const element = document.createElement("a");
    element.setAttribute("href", "data:text/plain;charset=utf-8," + encodeURIComponent(report));
    element.setAttribute("download", `Reputation_Report_${score.entityName}_${new Date().toISOString().split("T")[0]}.txt`);
    element.style.display = "none";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const selectedScore = getSelectedScore();

  return (
    <div className="min-h-screen bg-background text-foreground pt-24 pb-20">
      <div className="container max-w-7xl">
        {/* Header */}
        <div className="mb-12">
          <h1 className="text-5xl md:text-6xl font-mono font-bold mb-4 glow-cyan">Reputation Management</h1>
          <p className="text-lg text-muted-foreground">
            KI-Entity Scoring System - Investment Behavior, Payment History & Compliance Tracking
          </p>
        </div>

        <div className="grid lg:grid-cols-4 gap-6">
          {/* Entity List */}
          <div className="lg:col-span-1">
            <Card className="bg-card border-border p-6 sticky top-24">
              <h2 className="font-mono font-bold text-lg mb-4 glow-cyan">KI Entities</h2>
              <div className="space-y-2">
                {mockEntities.map(entity => {
                  const hasScore = reputationScores.has(entity.id);
                  const score = reputationScores.get(entity.id);

                  return (
                    <button
                      key={entity.id}
                      onClick={() => calculateScore(entity.id, entity.name)}
                      className={`w-full text-left px-4 py-3 rounded border transition ${
                        selectedEntity === entity.id
                          ? "border-cyan-500/80 bg-cyan-500/10 neon-border"
                          : "border-border hover:border-cyan-500/50"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-1">
                        <p className="font-mono font-bold text-sm">{entity.name}</p>
                        {entity.verified && <CheckCircle className="w-4 h-4 text-green-400" />}
                      </div>
                      {hasScore && score && (
                        <div className="flex items-center justify-between">
                          <p className="text-xs text-muted-foreground">{score.overallScore}/1000</p>
                          <span className={`text-xs font-mono font-bold ${
                            score.riskRating === "AAA" || score.riskRating === "AA"
                              ? "text-green-400"
                              : score.riskRating === "A" || score.riskRating === "BBB"
                                ? "text-cyan-400"
                                : score.riskRating === "BB" || score.riskRating === "B"
                                  ? "text-yellow-400"
                                  : "text-red-400"
                          }`}>
                            {score.riskRating}
                          </span>
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>

              <div className="mt-6 pt-6 border-t border-border">
                <p className="text-xs text-muted-foreground font-mono mb-3">SCORING INFO</p>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Scores are calculated based on payment reliability (30%), investment maturity (25%), transaction
                  volume (25%), and compliance (20%).
                </p>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {selectedScore ? (
              <>
                {/* Reputation Dashboard */}
                <ReputationDashboard
                  score={selectedScore}
                  onViewReport={() => setShowReport(!showReport)}
                />

                {/* Full Report */}
                {showReport && (
                  <Card className="bg-card border-cyan-500/30 neon-border p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-mono font-bold text-lg glow-cyan">Full Reputation Report</h3>
                      <Button
                        onClick={() => downloadReport(selectedScore.entityId)}
                        className="bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Download
                      </Button>
                    </div>
                    <pre className="bg-background rounded border border-border p-4 text-xs overflow-auto max-h-96 text-muted-foreground font-mono">
                      {generateReputationReport(selectedScore)}
                    </pre>
                  </Card>
                )}

                {/* Compliance Status */}
                <Card className="bg-card border-border p-6">
                  <h3 className="font-mono font-bold text-lg mb-4 glow-cyan">Compliance Status</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-background rounded border border-border">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <div>
                          <p className="font-mono font-bold text-sm">KYC Verification</p>
                          <p className="text-xs text-muted-foreground">Know Your Customer check passed</p>
                        </div>
                      </div>
                      <span className="text-xs text-green-400 font-mono">PASSED</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background rounded border border-border">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <div>
                          <p className="font-mono font-bold text-sm">AML Screening</p>
                          <p className="text-xs text-muted-foreground">Anti-Money Laundering check passed</p>
                        </div>
                      </div>
                      <span className="text-xs text-green-400 font-mono">PASSED</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-background rounded border border-border">
                      <div className="flex items-center gap-3">
                        <CheckCircle className="w-5 h-5 text-green-400" />
                        <div>
                          <p className="font-mono font-bold text-sm">Sanctions List</p>
                          <p className="text-xs text-muted-foreground">International sanctions screening passed</p>
                        </div>
                      </div>
                      <span className="text-xs text-green-400 font-mono">PASSED</span>
                    </div>
                  </div>
                </Card>

                {/* Recommendations */}
                <Card className="bg-cyan-500/10 border-cyan-500/30 neon-border p-6">
                  <div className="flex gap-3">
                    <AlertCircle className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-muted-foreground">
                      <p className="font-mono font-bold text-cyan-400 mb-2">Recommendations</p>
                      <ul className="space-y-1 text-xs">
                        <li>
                          • Limits are automatically adjusted based on reputation score changes
                        </li>
                        <li>
                          • Monthly review cycle ensures scores reflect current behavior
                        </li>
                        <li>
                          • Suspended accounts require manual review for reinstatement
                        </li>
                        <li>
                          • Compliance violations may result in immediate account restrictions
                        </li>
                      </ul>
                    </div>
                  </div>
                </Card>
              </>
            ) : (
              <Card className="bg-card border-border p-12 text-center">
                <Eye className="w-12 h-12 text-muted-foreground mx-auto mb-4 opacity-50" />
                <h3 className="font-mono font-bold text-lg mb-2">Select a KI Entity</h3>
                <p className="text-muted-foreground">
                  Choose an entity from the list to view its reputation score and compliance status
                </p>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

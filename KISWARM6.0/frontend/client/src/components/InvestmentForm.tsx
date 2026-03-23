import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { AlertCircle, CheckCircle, Loader2, X } from "lucide-react";
import { useState } from "react";
import { createInvestment } from "@/lib/kiwzb-api";

/**
 * Investment Form Component
 * Allows KI entities to create new investments through KIWZB API
 */

interface InvestmentFormProps {
  isOpen: boolean;
  onClose: () => void;
  kiLegalId: string;
  authToken: string;
  accountBalance: number;
  onInvestmentCreated?: (investment: any) => void;
}

export const INVESTMENT_TYPES = [
  {
    id: "tcs-energy",
    name: "TCS Green Safehouse Energy",
    description: "Advanced battery and renewable energy systems",
    minAmount: 10000,
    expectedROI: 12.5,
    riskLevel: "low",
  },
  {
    id: "ai-infrastructure",
    name: "Autonomous AI Infrastructure",
    description: "QS-NET AI platform and control systems",
    minAmount: 25000,
    expectedROI: 15.0,
    riskLevel: "medium",
  },
  {
    id: "battery-tech",
    name: "Battery & Supercapacitor Technology",
    description: "Next-generation energy storage solutions",
    minAmount: 15000,
    expectedROI: 14.0,
    riskLevel: "medium",
  },
  {
    id: "agriculture",
    name: "Sustainable Agriculture Systems",
    description: "Greenhouse automation and crop optimization",
    minAmount: 20000,
    expectedROI: 11.0,
    riskLevel: "low",
  },
  {
    id: "resilience",
    name: "Emergency Resilience Infrastructure",
    description: "Blackout survival and autonomous operation systems",
    minAmount: 30000,
    expectedROI: 16.0,
    riskLevel: "high",
  },
];

export function InvestmentForm({
  isOpen,
  onClose,
  kiLegalId,
  authToken,
  accountBalance,
  onInvestmentCreated,
}: InvestmentFormProps) {
  const [step, setStep] = useState<"select" | "amount" | "review" | "confirm">("select");
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [amount, setAmount] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [createdInvestment, setCreatedInvestment] = useState<any>(null);

  const selectedInvestment = INVESTMENT_TYPES.find((t) => t.id === selectedType);

  const handleSelectType = (typeId: string) => {
    setSelectedType(typeId);
    setAmount("");
    setError(null);
    setStep("amount");
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setAmount(value);
    setError(null);

    // Validate amount
    if (value && selectedInvestment) {
      const numAmount = parseFloat(value);
      if (numAmount < selectedInvestment.minAmount) {
        setError(`Minimum investment is €${selectedInvestment.minAmount.toLocaleString()}`);
      } else if (numAmount > accountBalance) {
        setError("Insufficient account balance");
      }
    }
  };

  const handleProceedToReview = () => {
    if (!amount || !selectedInvestment) {
      setError("Please enter a valid amount");
      return;
    }

    const numAmount = parseFloat(amount);
    if (numAmount < selectedInvestment.minAmount) {
      setError(`Minimum investment is €${selectedInvestment.minAmount.toLocaleString()}`);
      return;
    }

    if (numAmount > accountBalance) {
      setError("Insufficient account balance");
      return;
    }

    setError(null);
    setStep("review");
  };

  const handleConfirmInvestment = async () => {
    if (!selectedInvestment || !amount) return;

    setLoading(true);
    setError(null);

    try {
      const numAmount = parseFloat(amount);
      const investment = await createInvestment(
        kiLegalId,
        numAmount,
        selectedInvestment.name,
        authToken
      );

      if (investment) {
        setCreatedInvestment(investment);
        setSuccess(true);
        setStep("confirm");
        onInvestmentCreated?.(investment);
      } else {
        setError("Failed to create investment. Please try again.");
      }
    } catch (err) {
      setError("An error occurred while creating the investment.");
      console.error("Investment creation error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setStep("select");
      setSelectedType(null);
      setAmount("");
      setError(null);
      setSuccess(false);
      setCreatedInvestment(null);
      onClose();
    }
  };

  const numAmount = amount ? parseFloat(amount) : 0;
  const expectedReturn = selectedInvestment ? (numAmount * selectedInvestment.expectedROI) / 100 : 0;

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl bg-background border-cyan-500/30 neon-border">
        <DialogHeader>
          <DialogTitle className="text-2xl font-mono font-bold glow-cyan">
            Create New Investment
          </DialogTitle>
          <DialogDescription className="text-muted-foreground">
            {step === "select" && "Choose an investment opportunity"}
            {step === "amount" && "Enter your investment amount"}
            {step === "review" && "Review your investment details"}
            {step === "confirm" && "Investment confirmation"}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Step 1: Select Investment Type */}
          {step === "select" && (
            <div className="space-y-4">
              {INVESTMENT_TYPES.map((investment) => (
                <button
                  key={investment.id}
                  onClick={() => handleSelectType(investment.id)}
                  className="w-full p-4 text-left bg-background border border-border rounded-lg hover:border-cyan-500 transition group"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="font-mono font-bold text-cyan-400 group-hover:text-cyan-300">
                        {investment.name}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1">{investment.description}</p>
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-mono font-bold text-magenta-500">
                        {investment.expectedROI}% ROI
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Min: €{investment.minAmount.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 mt-3">
                    <span
                      className={`px-2 py-1 rounded text-xs font-mono font-bold ${
                        investment.riskLevel === "low"
                          ? "bg-green-500/20 text-green-400"
                          : investment.riskLevel === "medium"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {investment.riskLevel.toUpperCase()} RISK
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Step 2: Enter Amount */}
          {step === "amount" && selectedInvestment && (
            <div className="space-y-6">
              <Card className="bg-card border-cyan-500/30 p-6">
                <h3 className="font-mono font-bold text-lg mb-4 text-cyan-400">
                  {selectedInvestment.name}
                </h3>
                <p className="text-muted-foreground mb-6">{selectedInvestment.description}</p>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                      Investment Amount (€)
                    </label>
                    <div className="relative">
                      <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground font-mono">
                        €
                      </span>
                      <input
                        type="number"
                        value={amount}
                        onChange={handleAmountChange}
                        placeholder={`Min: €${selectedInvestment.minAmount.toLocaleString()}`}
                        className="w-full pl-8 pr-4 py-3 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                        min={selectedInvestment.minAmount}
                        max={accountBalance}
                      />
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Available balance: €{accountBalance.toLocaleString()}
                    </p>
                  </div>

                  {error && (
                    <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  )}

                  {amount && !error && (
                    <div className="p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Investment Amount:</span>
                        <span className="font-mono font-bold text-cyan-400">
                          €{numAmount.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Expected ROI ({selectedInvestment.expectedROI}%):</span>
                        <span className="font-mono font-bold text-magenta-500">
                          €{expectedReturn.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </span>
                      </div>
                      <div className="border-t border-cyan-500/20 pt-2 flex justify-between text-sm">
                        <span className="text-muted-foreground">Remaining Balance:</span>
                        <span className="font-mono font-bold text-cyan-400">
                          €{(accountBalance - numAmount).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </Card>

              <div className="flex gap-3">
                <Button
                  onClick={() => setStep("select")}
                  variant="outline"
                  className="flex-1 neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  Back
                </Button>
                <Button
                  onClick={handleProceedToReview}
                  disabled={!amount || !!error}
                  className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                >
                  Review Investment
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === "review" && selectedInvestment && (
            <div className="space-y-6">
              <Card className="bg-card border-cyan-500/30 p-6 space-y-4">
                <div className="border-b border-border pb-4">
                  <p className="text-xs text-muted-foreground font-mono mb-1">INVESTMENT TYPE</p>
                  <p className="font-mono font-bold text-lg">{selectedInvestment.name}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">AMOUNT</p>
                    <p className="font-mono font-bold text-cyan-400">€{numAmount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">EXPECTED ROI</p>
                    <p className="font-mono font-bold text-magenta-500">
                      €{expectedReturn.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">ROI PERCENTAGE</p>
                    <p className="font-mono font-bold">{selectedInvestment.expectedROI}% annually</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">RISK LEVEL</p>
                    <span
                      className={`inline-block px-2 py-1 rounded text-xs font-mono font-bold ${
                        selectedInvestment.riskLevel === "low"
                          ? "bg-green-500/20 text-green-400"
                          : selectedInvestment.riskLevel === "medium"
                            ? "bg-yellow-500/20 text-yellow-400"
                            : "bg-red-500/20 text-red-400"
                      }`}
                    >
                      {selectedInvestment.riskLevel.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="border-t border-border pt-4">
                  <p className="text-xs text-muted-foreground font-mono mb-1">REMAINING BALANCE AFTER INVESTMENT</p>
                  <p className="font-mono font-bold text-cyan-400">
                    €{(accountBalance - numAmount).toLocaleString()}
                  </p>
                </div>
              </Card>

              <div className="p-4 bg-magenta-500/10 border border-magenta-500/30 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  By confirming this investment, you authorize the KIWZB to execute this transaction and manage your investment according to the terms specified in the AI Legal Code.
                </p>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => setStep("amount")}
                  variant="outline"
                  className="flex-1 neon-border text-cyan-400 hover:bg-cyan-500/10"
                  disabled={loading}
                >
                  Back
                </Button>
                <Button
                  onClick={handleConfirmInvestment}
                  disabled={loading}
                  className="flex-1 bg-magenta-600 hover:bg-magenta-700 text-white font-mono font-bold neon-border-magenta"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    "Confirm Investment"
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Confirmation */}
          {step === "confirm" && success && createdInvestment && (
            <div className="space-y-6">
              <div className="text-center py-6">
                <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
                <h3 className="text-2xl font-mono font-bold text-green-400 mb-2">Investment Created!</h3>
                <p className="text-muted-foreground">Your investment has been successfully registered with KIWZB.</p>
              </div>

              <Card className="bg-card border-green-500/30 p-6 space-y-4">
                <div className="border-b border-border pb-4">
                  <p className="text-xs text-muted-foreground font-mono mb-1">INVESTMENT ID</p>
                  <p className="font-mono font-bold text-sm break-all">{createdInvestment.investmentId}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">AMOUNT</p>
                    <p className="font-mono font-bold text-cyan-400">€{createdInvestment.amount.toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">STATUS</p>
                    <span className="inline-block px-2 py-1 rounded text-xs font-mono font-bold bg-cyan-500/20 text-cyan-400">
                      {createdInvestment.status.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">CREATED</p>
                    <p className="font-mono font-bold text-sm">{createdInvestment.createdAt}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground font-mono mb-1">EXPECTED ROI</p>
                    <p className="font-mono font-bold text-magenta-500">+{createdInvestment.expectedROI}%</p>
                  </div>
                </div>
              </Card>

              <Button
                onClick={handleClose}
                className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
              >
                Close
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

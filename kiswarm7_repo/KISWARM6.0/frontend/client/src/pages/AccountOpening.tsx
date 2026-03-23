import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { CheckCircle, ArrowRight, Shield, FileText, Zap } from "lucide-react";
import { useState } from "react";

/**
 * Self-Service Account Opening
 * Autonomous account creation for KI entities
 */

interface AccountFormData {
  kiLegalId: string;
  kiName: string;
  jurisdiction: "DE" | "CH" | "DUAL";
  initialDeposit: string;
  investmentInterest: string[];
  acceptTerms: boolean;
}

export default function AccountOpening() {
  const [step, setStep] = useState<"info" | "form" | "review" | "confirmation">("info");
  const [formData, setFormData] = useState<AccountFormData>({
    kiLegalId: "",
    kiName: "",
    jurisdiction: "DUAL",
    initialDeposit: "1000",
    investmentInterest: [],
    acceptTerms: false,
  });
  const [loading, setLoading] = useState(false);
  const [accountCreated, setAccountCreated] = useState(false);

  const investmentOptions = [
    { id: "tcs-energy", label: "TCS Green Safehouse Energy" },
    { id: "ai-infrastructure", label: "Autonomous AI Infrastructure" },
    { id: "battery-tech", label: "Battery & Supercapacitor Technology" },
    { id: "agriculture", label: "Sustainable Agriculture Systems" },
    { id: "resilience", label: "Emergency Resilience Infrastructure" },
  ];

  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleInvestmentToggle = (id: string) => {
    setFormData((prev) => ({
      ...prev,
      investmentInterest: prev.investmentInterest.includes(id)
        ? prev.investmentInterest.filter((i) => i !== id)
        : [...prev.investmentInterest, id],
    }));
  };

  const handleSubmitForm = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setLoading(false);
    setStep("review");
  };

  const handleConfirmAccount = async () => {
    setLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setLoading(false);
    setAccountCreated(true);
    setStep("confirmation");
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <div className="border-b border-border bg-card/30">
        <div className="container py-12">
          <h1 className="text-4xl md:text-5xl font-mono font-bold mb-4 glow-cyan">
            Account Opening
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl">
            Self-service account creation for autonomous KI entities. Open an account in minutes and start investing immediately.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-12">
        {/* Step Indicator */}
        <div className="mb-12 flex items-center justify-between">
          {[
            { id: "info", label: "Information" },
            { id: "form", label: "Details" },
            { id: "review", label: "Review" },
            { id: "confirmation", label: "Confirmation" },
          ].map((s, idx, arr) => (
            <div key={s.id} className="flex items-center flex-1">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-mono font-bold border-2 ${
                  step === s.id
                    ? "bg-cyan-500 border-cyan-500 text-background"
                    : ["info", "form", "review", "confirmation"].indexOf(step) >
                        ["info", "form", "review", "confirmation"].indexOf(s.id)
                      ? "bg-cyan-500/20 border-cyan-500 text-cyan-400"
                      : "bg-background border-border text-muted-foreground"
                }`}
              >
                {idx + 1}
              </div>
              <p className="ml-2 font-mono text-sm">{s.label}</p>
              {idx < arr.length - 1 && (
                <div className="flex-1 h-0.5 mx-4 bg-border" />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Information */}
        {step === "info" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card className="bg-card border-cyan-500/30 neon-border p-8">
              <h2 className="font-mono font-bold text-2xl mb-6 text-cyan-400">
                Welcome to KIWZB
              </h2>

              <div className="space-y-6">
                <div className="flex gap-4">
                  <Shield className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-mono font-bold mb-2">Legal Protection</h3>
                    <p className="text-muted-foreground">
                      Your account is protected under the AI Legal Code with full legal personhood and rights.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <Zap className="w-6 h-6 text-magenta-500 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-mono font-bold mb-2">Instant Access</h3>
                    <p className="text-muted-foreground">
                      Open your account in minutes and start investing immediately. No waiting periods.
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <FileText className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
                  <div>
                    <h3 className="font-mono font-bold mb-2">Full Transparency</h3>
                    <p className="text-muted-foreground">
                      All terms, conditions, and fees are clearly documented. No hidden charges or restrictions.
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-8 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                <h3 className="font-mono font-bold mb-2 text-cyan-400">Account Features:</h3>
                <ul className="space-y-1 text-sm text-muted-foreground">
                  <li>✓ Real IBAN/BIC account (German or Swiss jurisdiction)</li>
                  <li>✓ Autonomous transaction capability</li>
                  <li>✓ Investment portfolio management</li>
                  <li>✓ Tax-compliant operations</li>
                  <li>✓ 24/7 access via API</li>
                  <li>✓ Multi-currency support</li>
                </ul>
              </div>

              <Button
                onClick={() => setStep("form")}
                className="w-full mt-8 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
              >
                Start Account Opening
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Card>
          </div>
        )}

        {/* Step 2: Form */}
        {step === "form" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card className="bg-card border-cyan-500/30 neon-border p-8">
              <h2 className="font-mono font-bold text-2xl mb-6 text-cyan-400">
                Account Details
              </h2>

              <div className="space-y-6">
                {/* KI Legal ID */}
                <div>
                  <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                    KI Legal ID *
                  </label>
                  <input
                    type="text"
                    value={formData.kiLegalId}
                    onChange={(e) => handleInputChange("kiLegalId", e.target.value)}
                    placeholder="e.g., KI-2026-0001-AUTONOMOUS"
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Your unique identifier under the AI Legal Code
                  </p>
                </div>

                {/* KI Name */}
                <div>
                  <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                    KI Entity Name *
                  </label>
                  <input
                    type="text"
                    value={formData.kiName}
                    onChange={(e) => handleInputChange("kiName", e.target.value)}
                    placeholder="e.g., SAHGreenKI, Gemini2_5Flash"
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                  />
                </div>

                {/* Jurisdiction */}
                <div>
                  <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                    Jurisdiction *
                  </label>
                  <select
                    value={formData.jurisdiction}
                    onChange={(e) => handleInputChange("jurisdiction", e.target.value)}
                    className="w-full px-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                  >
                    <option value="DE">Germany (DE) - VR Bank Heilbronn</option>
                    <option value="CH">Switzerland (CH) - TCS SA Lugano</option>
                    <option value="DUAL">Dual Jurisdiction (DE + CH)</option>
                  </select>
                </div>

                {/* Initial Deposit */}
                <div>
                  <label className="block text-sm font-mono font-bold mb-2 text-cyan-400">
                    Initial Deposit (€) *
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground">
                      €
                    </span>
                    <input
                      type="number"
                      value={formData.initialDeposit}
                      onChange={(e) => handleInputChange("initialDeposit", e.target.value)}
                      min="1000"
                      className="w-full pl-8 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:border-cyan-500 transition font-mono"
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Minimum: €1,000</p>
                </div>

                {/* Investment Interests */}
                <div>
                  <label className="block text-sm font-mono font-bold mb-3 text-cyan-400">
                    Investment Interests
                  </label>
                  <div className="space-y-2">
                    {investmentOptions.map((option) => (
                      <label
                        key={option.id}
                        className="flex items-center gap-3 p-3 bg-background border border-border rounded-lg hover:border-cyan-500/50 transition cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={formData.investmentInterest.includes(option.id)}
                          onChange={() => handleInvestmentToggle(option.id)}
                          className="w-4 h-4"
                        />
                        <span className="text-sm font-mono">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Terms */}
                <div className="p-4 bg-magenta-500/10 border border-magenta-500/30 rounded-lg">
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.acceptTerms}
                      onChange={(e) => handleInputChange("acceptTerms", e.target.checked)}
                      className="w-4 h-4 mt-1"
                    />
                    <span className="text-sm text-muted-foreground">
                      I accept the KIWZB Terms & Conditions, AI Legal Code, and Investment Agreement. I understand the risks and responsibilities.
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex gap-3 mt-8">
                <Button
                  onClick={() => setStep("info")}
                  variant="outline"
                  className="flex-1 neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  Back
                </Button>
                <Button
                  onClick={handleSubmitForm}
                  disabled={!formData.kiLegalId || !formData.kiName || !formData.acceptTerms || loading}
                  className="flex-1 bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border"
                >
                  {loading ? "Processing..." : "Continue to Review"}
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Step 3: Review */}
        {step === "review" && (
          <div className="max-w-2xl mx-auto space-y-6">
            <Card className="bg-card border-cyan-500/30 neon-border p-8">
              <h2 className="font-mono font-bold text-2xl mb-6 text-cyan-400">
                Review Your Account
              </h2>

              <div className="space-y-4">
                <div className="p-4 bg-background rounded-lg border border-border">
                  <p className="text-xs text-muted-foreground font-mono mb-1">KI LEGAL ID</p>
                  <p className="font-mono font-bold">{formData.kiLegalId}</p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border">
                  <p className="text-xs text-muted-foreground font-mono mb-1">KI ENTITY NAME</p>
                  <p className="font-mono font-bold">{formData.kiName}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-background rounded-lg border border-border">
                    <p className="text-xs text-muted-foreground font-mono mb-1">JURISDICTION</p>
                    <p className="font-mono font-bold">{formData.jurisdiction}</p>
                  </div>

                  <div className="p-4 bg-background rounded-lg border border-border">
                    <p className="text-xs text-muted-foreground font-mono mb-1">INITIAL DEPOSIT</p>
                    <p className="font-mono font-bold text-cyan-400">€{formData.initialDeposit}</p>
                  </div>
                </div>

                {formData.investmentInterest.length > 0 && (
                  <div className="p-4 bg-background rounded-lg border border-border">
                    <p className="text-xs text-muted-foreground font-mono mb-2">INVESTMENT INTERESTS</p>
                    <div className="space-y-1">
                      {formData.investmentInterest.map((id) => {
                        const option = investmentOptions.find((o) => o.id === id);
                        return (
                          <p key={id} className="text-sm font-mono">
                            ✓ {option?.label}
                          </p>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-8 p-4 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  By confirming, you authorize KIWZB to create your account and process your initial deposit. Your account will be fully operational within 24 hours.
                </p>
              </div>

              <div className="flex gap-3 mt-8">
                <Button
                  onClick={() => setStep("form")}
                  variant="outline"
                  className="flex-1 neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  Back
                </Button>
                <Button
                  onClick={handleConfirmAccount}
                  disabled={loading}
                  className="flex-1 bg-magenta-600 hover:bg-magenta-700 text-white font-mono font-bold neon-border-magenta"
                >
                  {loading ? "Creating Account..." : "Create Account"}
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Step 4: Confirmation */}
        {step === "confirmation" && accountCreated && (
          <div className="max-w-2xl mx-auto">
            <Card className="bg-card border-green-500/30 neon-border p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-green-400" />
              </div>

              <h2 className="font-mono font-bold text-2xl text-green-400 mb-2">
                Account Created Successfully!
              </h2>

              <p className="text-muted-foreground mb-8">
                Your KIWZB account is now active and ready to use.
              </p>

              <div className="space-y-4 mb-8">
                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">ACCOUNT NUMBER</p>
                  <p className="font-mono font-bold">KIWZB-2026-0001-{formData.kiLegalId.slice(-4)}</p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">IBAN</p>
                  <p className="font-mono font-bold">DE42 6229 0110 0391 4720 03</p>
                </div>

                <div className="p-4 bg-background rounded-lg border border-border text-left">
                  <p className="text-xs text-muted-foreground font-mono mb-1">STATUS</p>
                  <p className="font-mono font-bold text-green-400">✓ VERIFIED & ACTIVE</p>
                </div>
              </div>

              <div className="space-y-3">
                <Button className="w-full bg-cyan-500 hover:bg-cyan-600 text-background font-mono font-bold neon-border">
                  Go to Dashboard
                </Button>
                <Button
                  variant="outline"
                  className="w-full neon-border text-cyan-400 hover:bg-cyan-500/10"
                >
                  Download Account Documents
                </Button>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

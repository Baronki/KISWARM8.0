import { Card } from "@/components/ui/card";
import { CheckCircle, Clock, AlertCircle, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { verifyPaymentStatus } from "@/lib/sepa-payment";

/**
 * Payment Status Tracker Component
 * Real-time tracking of SEPA payment processing status
 */

interface PaymentStatusTrackerProps {
  paymentId: string;
  orderId: string;
  amount: number;
  currency: string;
  reference: string;
  onStatusChange?: (status: "pending" | "processing" | "completed" | "failed") => void;
}

export default function PaymentStatusTracker({
  paymentId,
  orderId,
  amount,
  currency,
  reference,
  onStatusChange,
}: PaymentStatusTrackerProps) {
  const [status, setStatus] = useState<"pending" | "processing" | "completed" | "failed">("pending");
  const [isChecking, setIsChecking] = useState(false);
  const [lastChecked, setLastChecked] = useState<string | null>(null);

  const statusSteps = [
    { step: "pending", label: "Zahlung eingeleitet", description: "Payment initiated" },
    { step: "processing", label: "Wird verarbeitet", description: "Processing at bank" },
    { step: "completed", label: "Abgeschlossen", description: "Payment completed" },
  ];

  const checkStatus = async () => {
    setIsChecking(true);
    try {
      const newStatus = await verifyPaymentStatus(paymentId);
      setStatus(newStatus);
      setLastChecked(new Date().toLocaleTimeString());
      onStatusChange?.(newStatus);
    } catch (error) {
      console.error("Error checking payment status:", error);
      setStatus("failed");
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    // Auto-check status every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    return () => clearInterval(interval);
  }, [paymentId]);

  const getStatusIcon = (step: string) => {
    if (step === status) {
      return <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />;
    } else if (statusSteps.findIndex(s => s.step === step) < statusSteps.findIndex(s => s.step === status)) {
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    } else {
      return <Clock className="w-5 h-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case "completed":
        return "border-green-500/30 neon-border-green";
      case "processing":
        return "border-cyan-500/30 neon-border";
      case "failed":
        return "border-red-500/30 neon-border-red";
      default:
        return "border-yellow-500/30 neon-border-yellow";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "completed":
        return { label: "Abgeschlossen", color: "text-green-400" };
      case "processing":
        return { label: "Wird verarbeitet", color: "text-cyan-400" };
      case "failed":
        return { label: "Fehler", color: "text-red-400" };
      default:
        return { label: "Ausstehend", color: "text-yellow-400" };
    }
  };

  const statusText = getStatusText();

  return (
    <Card className={`bg-card ${getStatusColor()} p-6`}>
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-mono font-bold text-lg">Zahlungsstatus / Payment Status</h3>
          <span className={`font-mono font-bold ${statusText.color}`}>{statusText.label}</span>
        </div>
        <p className="text-sm text-muted-foreground">
          Bestellungs-ID / Order ID: <span className="font-mono">{orderId}</span>
        </p>
      </div>

      {/* Payment Details */}
      <div className="bg-background rounded border border-border p-4 mb-6 space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Zahlungsreferenz / Reference:</span>
          <span className="font-mono font-bold">{reference}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Betrag / Amount:</span>
          <span className="font-mono font-bold text-cyan-400">{amount.toLocaleString()} {currency}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Zahlungs-ID / Payment ID:</span>
          <span className="font-mono text-xs">{paymentId.substring(0, 16)}...</span>
        </div>
      </div>

      {/* Status Timeline */}
      <div className="mb-6">
        <p className="text-xs text-muted-foreground font-mono mb-4">VERARBEITUNGSSCHRITTE / PROCESSING STEPS</p>
        <div className="space-y-3">
          {statusSteps.map((step, index) => (
            <div key={step.step} className="flex items-start gap-3">
              <div className="mt-1">{getStatusIcon(step.step)}</div>
              <div className="flex-1">
                <p className="font-mono font-bold text-sm">{step.label}</p>
                <p className="text-xs text-muted-foreground">{step.description}</p>
              </div>
              {index < statusSteps.length - 1 && (
                <div className="absolute left-[22px] top-[60px] w-0.5 h-8 bg-border"></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Status Information */}
      {status === "completed" && (
        <Card className="bg-green-500/10 border-green-500/30 neon-border-green p-4 mb-6">
          <div className="flex gap-3">
            <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-mono font-bold text-green-400 mb-1">Zahlung erfolgreich</p>
              <p>Your payment has been successfully processed. Your order will be activated shortly.</p>
            </div>
          </div>
        </Card>
      )}

      {status === "processing" && (
        <Card className="bg-cyan-500/10 border-cyan-500/30 neon-border p-4 mb-6">
          <div className="flex gap-3">
            <Loader2 className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5 animate-spin" />
            <div className="text-sm text-muted-foreground">
              <p className="font-mono font-bold text-cyan-400 mb-1">Wird verarbeitet</p>
              <p>Your payment is being processed by the bank. This usually takes 1-2 business days.</p>
            </div>
          </div>
        </Card>
      )}

      {status === "failed" && (
        <Card className="bg-red-500/10 border-red-500/30 neon-border-red p-4 mb-6">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-mono font-bold text-red-400 mb-1">Zahlungsfehler</p>
              <p>There was an issue processing your payment. Please contact support or try again.</p>
            </div>
          </div>
        </Card>
      )}

      {/* Last Checked */}
      <div className="text-xs text-muted-foreground text-center">
        {lastChecked && <p>Zuletzt geprüft / Last checked: {lastChecked}</p>}
        <button
          onClick={checkStatus}
          disabled={isChecking}
          className="text-cyan-400 hover:text-cyan-300 transition font-mono mt-2"
        >
          {isChecking ? "Wird geprüft..." : "Status jetzt prüfen"}
        </button>
      </div>
    </Card>
  );
}
